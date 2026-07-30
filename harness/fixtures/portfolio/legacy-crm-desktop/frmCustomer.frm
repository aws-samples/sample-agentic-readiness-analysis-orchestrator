VERSION 5.00
Begin VB.Form frmCustomer
   Caption         =   "ACME Sales CRM - Customer"
   ClientHeight    =   4800
   ClientWidth     =   7200
   Begin VB.CommandButton cmdSave
      Caption         =   "Save"
   End
   Begin VB.TextBox txtName
   End
End
Attribute VB_Name = "frmCustomer"
' ACME Sales CRM - Customer maintenance form
' Author: Greg P., 2005. Last touched 2018.
' DO NOT change the .mdb path - field laptops are mapped to S:\
Option Explicit

Private Const DB_PATH As String = "S:\CRM\sales.mdb"
Private Const DB_PW As String = "crm2005pw"

Private cn As ADODB.Connection

Private Sub Form_Load()
    Set cn = New ADODB.Connection
    ' Jet OLEDB with database password embedded
    cn.Open "Provider=Microsoft.Jet.OLEDB.4.0;Data Source=" & DB_PATH & _
            ";Jet OLEDB:Database Password=" & DB_PW
End Sub

Private Sub cmdSave_Click()
    Dim sql As String
    ' String-concatenated SQL - no parameters (injection risk)
    sql = "INSERT INTO Customers (Name, CreatedBy, CreatedOn) VALUES ('" & _
          txtName.Text & "', '" & Environ("USERNAME") & "', Now())"
    On Error Resume Next   ' swallow all errors, classic VB6 style
    cn.Execute sql
    If Err.Number <> 0 Then
        MsgBox "Could not save (record may be locked). Try again.", vbExclamation
        Err.Clear
    End If
End Sub

Private Sub Form_Unload(Cancel As Integer)
    On Error Resume Next
    cn.Close
    Set cn = Nothing
End Sub
