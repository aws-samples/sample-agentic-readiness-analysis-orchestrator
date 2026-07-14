package com.acme.loan;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import org.apache.struts.action.Action;
import org.apache.struts.action.ActionForm;
import org.apache.struts.action.ActionForward;
import org.apache.struts.action.ActionMapping;

/**
 * Struts 1 Action for loan pricing and submission.
 * Author: D. Whitfield, 2010. Last change 2017 (added APR cap).
 * NOTE: Struts 1 Actions are singletons - keep all state local.
 */
public class LoanAction extends Action {

    // Connection details - also duplicated in db.properties
    private static final String DB_URL = "jdbc:oracle:thin:@dbprod01:1521:LOANDB";
    private static final String DB_USER = "loan_app";
    private static final String DB_PASS = "loanApp2010";

    public ActionForward execute(ActionMapping mapping, ActionForm form,
            HttpServletRequest request, HttpServletResponse response) throws Exception {

        LoanForm lf = (LoanForm) form;
        double principal = lf.getPrincipal();
        double rate = lf.getAnnualRate() / 100.0 / 12.0;
        int months = lf.getTermMonths();

        // Standard amortization formula
        double payment = principal * rate / (1 - Math.pow(1 + rate, -months));
        lf.setMonthlyPayment(payment);

        if ("submit".equals(lf.getAction())) {
            saveApplication(lf, request.getRemoteUser());
            return mapping.findForward("confirm");
        }
        return mapping.findForward("quote");
    }

    private void saveApplication(LoanForm lf, String officer) throws Exception {
        Class.forName("oracle.jdbc.driver.OracleDriver");
        Connection cn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASS);
        // String-built SQL - applicant name not parameterized
        String sql = "INSERT INTO applications (applicant, principal, rate, term, officer) "
                + "VALUES ('" + lf.getApplicantName() + "', " + lf.getPrincipal() + ", "
                + lf.getAnnualRate() + ", " + lf.getTermMonths() + ", '" + officer + "')";
        PreparedStatement ps = cn.prepareStatement(sql);
        ps.executeUpdate();
        ps.close();
        cn.close();
    }
}
