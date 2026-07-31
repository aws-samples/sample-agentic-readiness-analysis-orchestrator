<!--- ACME Intranet Document Portal --->
<!--- Built 2007, last edited 2016. Datasource "docportal" set in CF Admin. --->
<cfapplication name="docportal" sessionmanagement="yes" sessiontimeout="#CreateTimeSpan(0,0,30,0)#">

<cfif NOT structKeyExists(session, "userid")>
    <cflocation url="login.cfm" addtoken="no">
</cfif>

<cfparam name="url.q" default="">

<html>
<head><title>ACME Document Portal</title></head>
<body bgcolor="#FFFFFF">
<h1>ACME Document Portal</h1>
<p>Welcome, <cfoutput>#session.fullname#</cfoutput></p>

<form action="index.cfm" method="get">
  Search: <input type="text" name="q" value="<cfoutput>#url.q#</cfoutput>">
  <input type="submit" value="Find">
</form>

<!--- SQL built by string concatenation - injection vulnerable --->
<cfquery name="docs" datasource="docportal">
    SELECT doc_id, title, category, uploaded_by, uploaded_on
    FROM documents
    WHERE title LIKE '%#url.q#%'
    ORDER BY uploaded_on DESC
</cfquery>

<table border="1" cellpadding="4">
  <tr><th>Title</th><th>Category</th><th>Uploaded By</th><th>Date</th></tr>
  <cfoutput query="docs">
  <tr>
    <td><a href="download.cfm?id=#doc_id#">#title#</a></td>
    <td>#category#</td>
    <td>#uploaded_by#</td>
    <td>#dateFormat(uploaded_on, 'mm/dd/yyyy')#</td>
  </tr>
  </cfoutput>
</table>

<hr>
<small>ACME Document Portal v2.3 | ColdFusion 8 | &copy; 2007</small>
</body>
</html>
