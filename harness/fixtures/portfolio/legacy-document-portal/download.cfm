<!--- File download handler - serves files from local disk --->
<!--- KNOWN ISSUE: filename comes straight from DB, path traversal possible --->
<cfquery name="doc" datasource="docportal">
    SELECT filename FROM documents WHERE doc_id = #url.id#
</cfquery>

<cfset filepath = "D:\docroot\files\" & doc.filename>

<cfheader name="Content-Disposition" value="attachment; filename=#doc.filename#">
<cfcontent type="application/octet-stream" file="#filepath#" deletefile="no">
