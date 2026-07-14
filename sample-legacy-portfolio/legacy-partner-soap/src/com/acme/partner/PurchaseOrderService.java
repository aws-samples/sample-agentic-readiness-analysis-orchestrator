package com.acme.partner;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import javax.jws.WebService;
import javax.jws.WebMethod;
import javax.jws.WebParam;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;

/**
 * JAX-WS SOAP endpoint for partner purchase order submission.
 * Author: P. Castellano, 2009. Last change 2016.
 * Deployed on JBoss 5.1, Java 6.
 */
@WebService(serviceName = "PurchaseOrderService", targetNamespace = "http://acme.com/partner")
public class PurchaseOrderService {

    private static final String DB_URL = "jdbc:oracle:thin:@10.0.9.30:1521:PARTDB";
    private static final String DB_USER = "partner_app";
    private static final String DB_PASS = "partner2009";

    @WebMethod
    public String submitOrder(@WebParam(name = "partnerId") String partnerId,
                              @WebParam(name = "poXml") String poXml) {
        try {
            // XML parsed with no XXE protection (external entities allowed)
            DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
            DocumentBuilder db = dbf.newDocumentBuilder();
            Document doc = db.parse(new java.io.ByteArrayInputStream(poXml.getBytes()));

            String poNumber = doc.getElementsByTagName("poNumber").item(0).getTextContent();
            String amount = doc.getElementsByTagName("amount").item(0).getTextContent();

            Class.forName("oracle.jdbc.driver.OracleDriver");
            Connection cn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASS);
            Statement st = cn.createStatement();
            // String-built SQL straight from parsed XML - injection risk
            st.executeUpdate("INSERT INTO partner_orders (partner_id, po_number, amount) VALUES ('"
                    + partnerId + "', '" + poNumber + "', " + amount + ")");
            st.close();
            cn.close();
            return "ACCEPTED:" + poNumber;
        } catch (Exception e) {
            // return raw exception text to the caller
            return "ERROR:" + e.getMessage();
        }
    }
}
