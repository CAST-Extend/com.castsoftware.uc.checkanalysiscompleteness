import cast_upgrade_1_5_10 # @UnusedImport @UnresolvedImport
from cast.application import ApplicationLevelExtension, CASTAIP # @UnresolvedImport

import logging
import xlsxwriter
import unanalysed
import os


def main(application, report_path, version=None):
    
    workbook = xlsxwriter.Workbook(report_path)
    percentage = unanalysed.generate_report(application, workbook, version)
    workbook.close()
    
    # try to send report by email
    mngt_application = application.get_application_configuration()
    if mngt_application:
        try:
            address = mngt_application.get_email_to_send_reports()
            
            if address:
                
                logging.info('Sending report by mail to %s', address)
                
                caip = CASTAIP.get_running_caip()
                
                # Import the email modules we'll need
                from email.mime.text import MIMEText
                from email.mime.base import MIMEBase
                from email import encoders
                from email.mime.multipart import MIMEMultipart
                
                # Open a plain text file for reading.  For this example, assume that
                # the text file contains only ASCII characters.
                
                msg = MIMEMultipart()
                
                msg['From'] = 'Unanalysed Code Report<' + caip.get_mail_from_address() + '>'
                msg['To'] = address
    
                msg['Subject'] = 'Unanalysed Code Report for %s' % application.get_name()
                
                # message body
                html = """\
                <html>
                  <head></head>
                  <body>
                    <p>Percentage of unanalysed files: %s%%<br>
                    See attachement for full details.<br>
                    <a href="https://github.com/CAST-Extend/com.castsoftware.uc.checkanalysiscompleteness/blob/master/readme.md">Usage documentation</a> 
                    </p>
                  </body>
                </html>
                """  % percentage
                
                msg.attach(MIMEText(html, 'html'))
                
                # attach report
                part = MIMEBase('application', "octet-stream")
                part.set_payload(open(report_path, "rb").read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="completeness_report.xlsx"')
                msg.attach(part)
                
                server = caip.get_mail_server()
                
                server.send_message(msg)
                server.quit()
                logging.info('Mail sent')
            
        except Exception as e:
            logging.warning(e)
            pass
    

class CheckApplication(ApplicationLevelExtension):

    def end_application(self, application):
        
        logging.info("##################################################################")
        logging.info("Checking application completeness")
        
        self.get_plugin().get_version()
        report_path = os.path.join(self.get_plugin().intermediate, 'completeness_report.xlsx')
        
        # make path usable directly in windows
        report_path = report_path.replace('/', '\\')
        
        main(application, report_path)
        
        logging.info("Generated report %s" % report_path)
        logging.info("##################################################################")
