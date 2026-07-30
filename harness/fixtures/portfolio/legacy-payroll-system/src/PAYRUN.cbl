      ******************************************************************
      * PAYRUN - BIWEEKLY PAYROLL CALCULATION                          *
      * AUTHOR: R. ANDERSON (RETIRED 2014)                             *
      * LAST CHANGE: 2019-01-04  UPDATE FICA WAGE BASE FOR 2019        *
      * WARNING: DO NOT RECOMPILE WITHOUT CONTACTING MAINFRAME TEAM    *
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYRUN.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT EMP-FILE ASSIGN TO EMPMAST
               ORGANIZATION IS INDEXED
               ACCESS MODE IS SEQUENTIAL
               RECORD KEY IS EMP-ID.
           SELECT PAY-FILE ASSIGN TO PAYOUT
               ORGANIZATION IS SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD  EMP-FILE.
       01  EMP-RECORD.
           05  EMP-ID            PIC 9(09).
           05  EMP-NAME          PIC X(30).
           05  EMP-RATE          PIC 9(05)V99.
           05  EMP-HOURS         PIC 9(03)V99.
           05  EMP-SSN           PIC 9(09).
           05  EMP-ACCT          PIC X(17).
       FD  PAY-FILE.
       01  PAY-RECORD            PIC X(120).
       WORKING-STORAGE SECTION.
       01  WS-GROSS              PIC 9(07)V99.
       01  WS-FICA              PIC 9(07)V99.
       01  WS-FICA-RATE         PIC V9999 VALUE 0.0620.
       01  WS-WAGE-BASE         PIC 9(06)V99 VALUE 132900.00.
       01  WS-NET                PIC 9(07)V99.
       01  WS-EOF                PIC X VALUE 'N'.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT EMP-FILE.
           OPEN OUTPUT PAY-FILE.
           PERFORM READ-EMP.
           PERFORM PROCESS-EMP UNTIL WS-EOF = 'Y'.
           CLOSE EMP-FILE PAY-FILE.
           STOP RUN.
       PROCESS-EMP.
           COMPUTE WS-GROSS = EMP-RATE * EMP-HOURS.
           COMPUTE WS-FICA = WS-GROSS * WS-FICA-RATE.
           COMPUTE WS-NET = WS-GROSS - WS-FICA.
      *    NOTE: STATE TAX TABLE LOOKUP REMOVED IN 2011, DONE MANUALLY
           MOVE SPACES TO PAY-RECORD.
           STRING EMP-ID DELIMITED BY SIZE
                  EMP-NAME DELIMITED BY SIZE
                  WS-NET DELIMITED BY SIZE
               INTO PAY-RECORD.
           WRITE PAY-RECORD.
           PERFORM READ-EMP.
       READ-EMP.
           READ EMP-FILE
               AT END MOVE 'Y' TO WS-EOF.
