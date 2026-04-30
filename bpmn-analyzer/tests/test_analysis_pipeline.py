"""
Tests for the BPMN analysis pipeline.

Validates that the deterministic extraction (parsing, constraints, scoring)
produces correct and stable results from sample BPMN files.
"""
import json
import sys
from pathlib import Path

import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.bpmn_parser import parse_bpmn, BPMNProcess, ElementType
from analyzer.constraint_extractor import (
    extract_constraints,
    ConstraintProfile,
    ConstraintType,
)
from augmentor.task_evaluator import (
    evaluate_tasks,
    AugmentationPlan,
    MigrationType,
    ReplacementVerdict,
)
from run_analysis import analyze_bpmn

SAMPLES_DIR = Path(__file__).parent.parent / "samples"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
LOAN_BPMN = SAMPLES_DIR / "loan_approval.bpmn"
KYC_BPMN = SAMPLES_DIR / "kyc_onboarding.bpmn"


# ── Exception Handling Tests ──────────────────────────────────────────────────

from analyzer.exceptions import (
    BPMNAnalysisError,
    MalformedBPMN,
    UnsupportedBPMNVersion,
    AnalysisWarning,
)
from analyzer.dependency_extractor import extract_dependencies, to_dict, DependencyReport
import analyzer.vendors  # noqa: F401


class TestExceptionHandling:
    """Tests for robust error handling on unsupported versions/vendors."""

    # -- Parser-level exceptions --

    def test_malformed_xml_raises(self):
        """Malformed XML should raise MalformedBPMN, not a raw lxml error."""
        with pytest.raises(MalformedBPMN) as exc_info:
            parse_bpmn(str(FIXTURES_DIR / "malformed.bpmn"))
        assert "Not valid XML" in str(exc_info.value)
        assert exc_info.value.file_path != ""

    def test_nonexistent_file_raises_malformed(self):
        """Missing file should raise MalformedBPMN with context."""
        with pytest.raises(MalformedBPMN) as exc_info:
            parse_bpmn("/nonexistent/path/fake.bpmn")
        assert "Cannot read file" in str(exc_info.value)

    def test_no_process_element_raises_malformed(self):
        """Valid XML with no <process> should raise MalformedBPMN."""
        with pytest.raises(MalformedBPMN) as exc_info:
            parse_bpmn(str(FIXTURES_DIR / "no_process.bpmn"))
        assert "No <process> element" in str(exc_info.value)

    def test_bpmn_1x_raises_unsupported_version(self):
        """BPMN 1.x namespace should raise UnsupportedBPMNVersion."""
        with pytest.raises(UnsupportedBPMNVersion) as exc_info:
            parse_bpmn(str(FIXTURES_DIR / "bpmn1x.bpmn"))
        assert exc_info.value.detected_version == "1.0"
        assert "2.0" in exc_info.value.supported_versions

    def test_unsupported_version_has_structured_context(self):
        """UnsupportedBPMNVersion should carry structured context."""
        with pytest.raises(UnsupportedBPMNVersion) as exc_info:
            parse_bpmn(str(FIXTURES_DIR / "bpmn1x.bpmn"))
        ctx = exc_info.value.context
        assert ctx["detected_version"] == "1.0"
        assert "2.0" in ctx["supported_versions"]

    def test_exception_hierarchy(self):
        """All custom exceptions should be catchable as BPMNAnalysisError."""
        with pytest.raises(BPMNAnalysisError):
            parse_bpmn(str(FIXTURES_DIR / "malformed.bpmn"))
        with pytest.raises(BPMNAnalysisError):
            parse_bpmn(str(FIXTURES_DIR / "bpmn1x.bpmn"))

    # -- Dependency extractor: unsupported vendor warnings --

    def test_unknown_vendor_produces_warning(self):
        """BPMN with unregistered vendor namespace should produce a warning."""
        process = parse_bpmn(str(FIXTURES_DIR / "unknown_vendor.bpmn"))
        report = extract_dependencies(str(FIXTURES_DIR / "unknown_vendor.bpmn"), process)
        warning_codes = [w.code for w in report.warnings]
        assert "unsupported_vendor_namespace" in warning_codes

    def test_unknown_vendor_warning_has_namespace(self):
        """Warning should list the unmatched namespace."""
        process = parse_bpmn(str(FIXTURES_DIR / "unknown_vendor.bpmn"))
        report = extract_dependencies(str(FIXTURES_DIR / "unknown_vendor.bpmn"), process)
        ns_warning = next(w for w in report.warnings if w.code == "unsupported_vendor_namespace")
        assert "appian" in ns_warning.message.lower() or "appian" in str(ns_warning.details).lower()

    def test_unknown_vendor_warning_lists_registered(self):
        """Warning should list registered vendors for discoverability."""
        process = parse_bpmn(str(FIXTURES_DIR / "unknown_vendor.bpmn"))
        report = extract_dependencies(str(FIXTURES_DIR / "unknown_vendor.bpmn"), process)
        ns_warning = next(w for w in report.warnings if w.code == "unsupported_vendor_namespace")
        registered = ns_warning.details.get("registered_vendors", [])
        assert "camunda-c7" in registered
        assert "camunda-c8" in registered
        assert "jbpm" in registered

    def test_unknown_vendor_still_extracts_standard_deps(self):
        """Standard BPMN 2.0 extraction should still work even with unknown vendor."""
        process = parse_bpmn(str(FIXTURES_DIR / "unknown_vendor.bpmn"))
        report = extract_dependencies(str(FIXTURES_DIR / "unknown_vendor.bpmn"), process)
        # Should not crash, should return a valid report
        assert isinstance(report, DependencyReport)

    # -- Dependency extractor: malformed XML --

    def test_dep_extractor_malformed_xml_raises(self):
        """Dependency extractor should raise MalformedBPMN on bad XML."""
        dummy_process = BPMNProcess(id="x", name="x")
        with pytest.raises(MalformedBPMN):
            extract_dependencies(str(FIXTURES_DIR / "malformed.bpmn"), dummy_process)

    # -- Warnings serialization --

    def test_warnings_in_json_output(self):
        """Warnings should appear in to_dict output when present."""
        process = parse_bpmn(str(FIXTURES_DIR / "unknown_vendor.bpmn"))
        report = extract_dependencies(str(FIXTURES_DIR / "unknown_vendor.bpmn"), process)
        d = to_dict(report)
        assert "warnings" in d
        assert len(d["warnings"]) > 0
        assert d["warnings"][0]["code"] == "unsupported_vendor_namespace"

    def test_no_warnings_omitted_from_json(self):
        """When there are no warnings, the key should be absent (clean output)."""
        process = parse_bpmn(str(LOAN_BPMN))
        report = extract_dependencies(str(LOAN_BPMN), process)
        d = to_dict(report)
        assert "warnings" not in d

    def test_warning_to_dict_structure(self):
        """AnalysisWarning.to_dict should produce a clean JSON-serializable dict."""
        w = AnalysisWarning(
            code="test_code",
            message="test message",
            vendor="test-vendor",
            details={"key": "value"},
        )
        d = w.to_dict()
        assert d["code"] == "test_code"
        assert d["vendor"] == "test-vendor"
        assert d["details"]["key"] == "value"
        json.dumps(d)  # Should not raise

    # -- Full pipeline with errors --

    def test_full_pipeline_malformed_raises(self):
        """analyze_bpmn should propagate MalformedBPMN."""
        with pytest.raises(MalformedBPMN):
            analyze_bpmn(str(FIXTURES_DIR / "malformed.bpmn"))

    def test_full_pipeline_bpmn1x_raises(self):
        """analyze_bpmn should propagate UnsupportedBPMNVersion."""
        with pytest.raises(UnsupportedBPMNVersion):
            analyze_bpmn(str(FIXTURES_DIR / "bpmn1x.bpmn"))

    # -- Vendor auto-discovery resilience --

    def test_vendor_load_errors_accessible(self):
        """get_load_errors should return a list (empty if all loaded OK)."""
        from analyzer.vendors import get_load_errors
        errors = get_load_errors()
        assert isinstance(errors, list)


# ── Dependency Extractor Tests ────────────────────────────────────────────────


class TestDependencyExtractor:
    @pytest.fixture
    def loan_process(self):
        return parse_bpmn(str(LOAN_BPMN))

    @pytest.fixture
    def kyc_process(self):
        return parse_bpmn(str(KYC_BPMN))

    @pytest.fixture
    def loan_deps(self, loan_process):
        return extract_dependencies(str(LOAN_BPMN), loan_process)

    @pytest.fixture
    def kyc_deps(self, kyc_process):
        return extract_dependencies(str(KYC_BPMN), kyc_process)

    def test_returns_dependency_report(self, loan_deps):
        assert isinstance(loan_deps, DependencyReport)

    def test_loan_has_unknown_user_task(self, loan_deps):
        """Loan approval has a userTask (manual_review) with no system refs."""
        unknown_ids = [u.source_task_id for u in loan_deps.unknown]
        assert "manual_review" in unknown_ids

    def test_loan_detects_jbpm_vendor(self, loan_deps):
        """Loan approval uses drools namespace, jBPM extractor should fire."""
        vendors = {d.vendor for d in loan_deps.inferred}
        assert "jbpm" in vendors, "jBPM extractor should detect drools namespace"

    def test_loan_jbpm_package_dependency(self, loan_deps):
        """jBPM extractor should find drools:packageName."""
        pkg_deps = [
            d for d in loan_deps.inferred
            if d.vendor == "jbpm" and "java-package:" in d.target_ref
        ]
        assert len(pkg_deps) >= 1
        assert "com.example" in pkg_deps[0].target_ref

    @pytest.mark.skipif(not KYC_BPMN.exists(), reason="KYC sample not available")
    def test_kyc_has_no_vendor_deps(self, kyc_deps):
        """KYC uses standard BPMN 2.0 only, no vendor extractors should fire."""
        vendor_deps = [d for d in kyc_deps.inferred if d.vendor != "bpmn-2.0"]
        assert len(vendor_deps) == 0

    def test_serialization(self, loan_deps):
        """to_dict should produce a JSON-serializable structure."""
        d = to_dict(loan_deps)
        assert "declared" in d
        assert "inferred" in d
        assert "unknown" in d
        import json
        json.dumps(d)  # Should not raise

    def test_deduplication(self, loan_deps):
        """No duplicate (source_task_id, target_ref, target_type) tuples."""
        keys = [
            (d.source_task_id, d.target_ref, d.target_type)
            for d in loan_deps.inferred
        ]
        assert len(keys) == len(set(keys))


# ── Parser Tests ──────────────────────────────────────────────────────────────


class TestBPMNParser:
    def test_parse_loan_approval(self):
        process = parse_bpmn(str(LOAN_BPMN))
        assert isinstance(process, BPMNProcess)
        assert process.name == "loan_approval"
        assert len(process.elements) > 0
        assert len(process.flows) > 0

    def test_parse_returns_tasks(self):
        process = parse_bpmn(str(LOAN_BPMN))
        task_types = {
            ElementType.TASK,
            ElementType.SERVICE_TASK,
            ElementType.USER_TASK,
            ElementType.SCRIPT_TASK,
            ElementType.BUSINESS_RULE_TASK,
        }
        tasks = [
            e for e in process.elements.values() if e.element_type in task_types
        ]
        assert len(tasks) >= 1, "Should find at least one task"

    def test_parse_returns_gateways(self):
        process = parse_bpmn(str(LOAN_BPMN))
        gateway_types = {
            ElementType.EXCLUSIVE_GATEWAY,
            ElementType.PARALLEL_GATEWAY,
            ElementType.INCLUSIVE_GATEWAY,
        }
        gateways = [
            e for e in process.elements.values() if e.element_type in gateway_types
        ]
        assert len(gateways) >= 1, "Loan approval should have at least one gateway"

    def test_parse_has_start_and_end(self):
        process = parse_bpmn(str(LOAN_BPMN))
        assert len(process.start_events) >= 1
        assert len(process.end_events) >= 1

    @pytest.mark.skipif(not KYC_BPMN.exists(), reason="KYC sample not available")
    def test_parse_kyc_onboarding(self):
        process = parse_bpmn(str(KYC_BPMN))
        assert isinstance(process, BPMNProcess)
        assert len(process.elements) > 0

    def test_parse_nonexistent_file_raises(self):
        with pytest.raises(MalformedBPMN):
            parse_bpmn("/nonexistent/file.bpmn")


# ── Constraint Extractor Tests ────────────────────────────────────────────────


class TestConstraintExtractor:
    @pytest.fixture
    def loan_process(self):
        return parse_bpmn(str(LOAN_BPMN))

    @pytest.fixture
    def loan_constraints(self, loan_process):
        return extract_constraints(loan_process)

    def test_extracts_constraints(self, loan_constraints):
        assert isinstance(loan_constraints, ConstraintProfile)
        assert loan_constraints.total_constraints > 0

    def test_constraint_density_positive(self, loan_constraints):
        assert loan_constraints.constraint_density > 0

    def test_has_init_constraints(self, loan_constraints):
        init = [
            c
            for c in loan_constraints.constraints
            if c.constraint_type == ConstraintType.INIT
        ]
        assert len(init) >= 1, "Should have at least one INIT constraint"

    def test_has_end_constraints(self, loan_constraints):
        end = [
            c
            for c in loan_constraints.constraints
            if c.constraint_type == ConstraintType.END
        ]
        assert len(end) >= 1, "Should have at least one END constraint"

    def test_has_succession_constraints(self, loan_constraints):
        succession = [
            c
            for c in loan_constraints.constraints
            if c.constraint_type == ConstraintType.SUCCESSION
        ]
        assert len(succession) >= 1, "Sequential process should have succession constraints"

    def test_has_exclusive_choice(self, loan_constraints):
        """Loan approval has XOR gateways, should produce exclusive choice constraints."""
        exclusive = [
            c
            for c in loan_constraints.constraints
            if c.constraint_type == ConstraintType.EXCLUSIVE_CHOICE
        ]
        assert len(exclusive) >= 1, "XOR gateways should produce exclusive choice constraints"

    def test_gateway_depth(self, loan_constraints):
        assert loan_constraints.max_gateway_depth >= 1

    def test_constraints_are_deduplicated(self, loan_constraints):
        keys = [
            (c.constraint_type, c.source, c.target)
            for c in loan_constraints.constraints
        ]
        assert len(keys) == len(set(keys)), "Constraints should be deduplicated"

    def test_signal_formulas(self, loan_constraints):
        for c in loan_constraints.constraints[:5]:
            signal = c.to_signal()
            assert isinstance(signal, str)
            assert len(signal) > 0
            assert "UNSUPPORTED" not in signal

    def test_ltlf_formulas(self, loan_constraints):
        for c in loan_constraints.constraints[:5]:
            ltlf = c.to_ltlf()
            assert isinstance(ltlf, str)
            assert len(ltlf) > 0

    def test_serialization_roundtrip(self, loan_constraints):
        d = loan_constraints.to_dict()
        restored = ConstraintProfile.from_dict(d)
        assert restored.process_name == loan_constraints.process_name
        assert restored.total_constraints == loan_constraints.total_constraints
        assert restored.total_elements == loan_constraints.total_elements


# ── Task Evaluator Tests ──────────────────────────────────────────────────────


class TestTaskEvaluator:
    @pytest.fixture
    def loan_plan(self):
        process = parse_bpmn(str(LOAN_BPMN))
        constraints = extract_constraints(process)
        return evaluate_tasks(process, constraints)

    def test_evaluates_all_tasks(self, loan_plan):
        assert isinstance(loan_plan, AugmentationPlan)
        assert loan_plan.total_tasks >= 1

    def test_classification_coverage(self, loan_plan):
        """Every task should be classified as agent, service, or human."""
        total = loan_plan.agent_count + loan_plan.service_count + loan_plan.human_count
        assert total == loan_plan.total_tasks

    def test_scores_in_range(self, loan_plan):
        for e in loan_plan.evaluations:
            assert 0.0 <= e.score.ai_benefit <= 1.0
            assert 0.0 <= e.score.complexity <= 1.0
            assert 0.0 <= e.score.risk <= 1.0
            assert 0.0 <= e.score.effort <= 1.0

    def test_composite_score_formula(self, loan_plan):
        for e in loan_plan.evaluations:
            expected = (
                0.40 * e.score.ai_benefit
                + 0.15 * e.score.complexity
                - 0.30 * e.score.risk
                - 0.15 * e.score.effort
            )
            assert abs(e.score.composite - expected) < 0.01

    def test_evaluations_sorted_by_composite(self, loan_plan):
        composites = [e.score.composite for e in loan_plan.evaluations]
        assert composites == sorted(composites, reverse=True)

    def test_agent_tasks_have_cost_estimates(self, loan_plan):
        for e in loan_plan.evaluations:
            if e.migration_type == MigrationType.AGENT:
                assert e.cost_estimate is not None
                assert e.cost_estimate.estimated_tokens_per_invocation > 0
                assert e.cost_estimate.cost_per_1k_invocations_usd >= 0

    def test_verdict_values(self, loan_plan):
        valid = {v.value for v in ReplacementVerdict}
        for e in loan_plan.evaluations:
            assert e.verdict.value in valid

    def test_migration_type_values(self, loan_plan):
        valid = {v.value for v in MigrationType}
        for e in loan_plan.evaluations:
            assert e.migration_type.value in valid


# ── Full Pipeline Tests ───────────────────────────────────────────────────────


class TestFullPipeline:
    def test_analyze_bpmn_returns_valid_json(self):
        result = analyze_bpmn(str(LOAN_BPMN))
        assert "process" in result
        assert "constraints" in result
        assert "tasks" in result
        assert "dependencies" in result
        assert "summary" in result

    def test_dependencies_structure(self):
        result = analyze_bpmn(str(LOAN_BPMN))
        deps = result["dependencies"]
        assert "declared" in deps
        assert "inferred" in deps
        assert "unknown" in deps
        assert isinstance(deps["declared"], list)
        assert isinstance(deps["inferred"], list)
        assert isinstance(deps["unknown"], list)

    def test_process_metadata(self):
        result = analyze_bpmn(str(LOAN_BPMN))
        assert result["process"]["name"] == "loan_approval"
        assert result["process"]["total_elements"] > 0
        assert result["process"]["total_flows"] > 0

    def test_constraints_metadata(self):
        result = analyze_bpmn(str(LOAN_BPMN))
        assert result["constraints"]["total"] > 0
        assert result["constraints"]["density"] > 0

    def test_tasks_have_required_fields(self):
        result = analyze_bpmn(str(LOAN_BPMN))
        for task in result["tasks"]:
            assert "element_id" in task
            assert "element_name" in task
            assert "element_type" in task
            assert "scores" in task
            assert "migration_type" in task
            assert task["scores"]["ai_benefit"] >= 0
            assert task["scores"]["risk"] >= 0

    def test_summary_counts_match(self):
        result = analyze_bpmn(str(LOAN_BPMN))
        total = (
            result["summary"]["agent_count"]
            + result["summary"]["service_count"]
            + result["summary"]["human_count"]
        )
        assert total == result["summary"]["total_tasks"]

    def test_json_serializable(self):
        result = analyze_bpmn(str(LOAN_BPMN))
        serialized = json.dumps(result)
        deserialized = json.loads(serialized)
        assert deserialized["process"]["name"] == "loan_approval"

    def test_deterministic_output(self):
        """Running the same BPMN file twice should produce identical results."""
        result1 = analyze_bpmn(str(LOAN_BPMN))
        result2 = analyze_bpmn(str(LOAN_BPMN))
        assert result1 == result2

    def test_custom_volume(self):
        result = analyze_bpmn(str(LOAN_BPMN), daily_volume=500)
        assert result["summary"]["total_estimated_monthly_cost_usd"] >= 0
