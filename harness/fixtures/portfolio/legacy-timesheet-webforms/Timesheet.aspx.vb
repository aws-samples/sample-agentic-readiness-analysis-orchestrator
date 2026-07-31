' Timesheet entry code-behind - ASP.NET 2.0 / VB.NET
' Author: M. Reilly, 2006. Last change 2015.
Imports System
Imports System.Data
Imports System.Data.SqlClient
Imports System.Configuration

Partial Class Timesheet
    Inherits System.Web.UI.Page

    Private connStr As String = ConfigurationManager.ConnectionStrings("TimesheetDB").ConnectionString

    Protected Sub Page_Load(ByVal sender As Object, ByVal e As EventArgs) Handles Me.Load
        If Not IsPostBack Then
            BindGrid()
        End If
    End Sub

    Private Sub BindGrid()
        Dim empId As String = Session("EmployeeId")
        Using cn As New SqlConnection(connStr)
            cn.Open()
            ' String-concatenated SQL - injection risk
            Dim sql As String = "SELECT entry_date, hours, project FROM timesheets " & _
                                "WHERE employee_id = '" & empId & "' ORDER BY entry_date DESC"
            Dim cmd As New SqlCommand(sql, cn)
            Dim da As New SqlDataAdapter(cmd)
            Dim dt As New DataTable()
            da.Fill(dt)
            gridEntries.DataSource = dt
            gridEntries.DataBind()
        End Using
    End Sub

    Protected Sub btnSave_Click(ByVal sender As Object, ByVal e As EventArgs)
        Using cn As New SqlConnection(connStr)
            cn.Open()
            Dim sql As String = "INSERT INTO timesheets (employee_id, entry_date, hours, project) " & _
                                "VALUES ('" & Session("EmployeeId") & "', '" & txtDate.Text & "', " & _
                                txtHours.Text & ", '" & txtProject.Text & "')"
            Dim cmd As New SqlCommand(sql, cn)
            cmd.ExecuteNonQuery()
        End Using
        BindGrid()
    End Sub
End Class
