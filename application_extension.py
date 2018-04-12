import cast_upgrade_1_5_17 # @UnusedImport @UnresolvedImport
from cast.application import ApplicationLevelExtension, CASTAIP # @UnresolvedImport

import glob
import logging
import xlsxwriter
import xlrd
import unanalysed
import os
import time


def main(application, report_path, version=None, previously_unanalysed=set()):
    
    # Generate the Excel report and get the raw percentage
    workbook = xlsxwriter.Workbook(report_path)
    percentage = unanalysed.generate_report(application, workbook, version, previously_unanalysed)
    workbook.close()

    try:
        # try Publish the Execution Report in CMS
        report_name='Unanalyzed Code'
        metric_name = 'Percentage of unanalysed files'
        metric='%.1f%%' % percentage
        level='OK'
        if (percentage > 10):
            level='Warning'
        
        # this import may fail in versions < 8.3
        from cast.application import publish_report # @UnresolvedImport
        publish_report(report_name, level, metric_name, metric, detail_report_path=report_path)
    
    except:
        pass # probably not in 8.3
    
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


def find_latest_report(folder):
    """
    Return the latest resport in the given folder
    """
    pathes = list(glob.glob(os.path.join(folder, "completeness_report_*.xlsx")))
    pathes.sort()
    if pathes:
        return pathes[-1]
    

def load_previously_unanalysed_files(folder):
    """
    Give the set of unanalysed files in the previous run 
    """
    path = find_latest_report(folder)
    
    result = set()
    
    if path:
        
        try:
            xl_workbook = xlrd.open_workbook(path)
            xl_sheet = xl_workbook.sheet_by_name('Files Not Analyzed')
            for row_idx in range(1, xl_sheet.nrows):
                
                path = xl_sheet.cell(row_idx, 1)
                result.add(path.value)
        except:
            pass
    
    return result


class CheckApplication(ApplicationLevelExtension):

    def end_application(self, application):
        
        logging.info("##################################################################")
        logging.info("Checking application completeness")
        
        self.get_plugin().get_version()
        report_path = os.path.join(self.get_plugin().intermediate, time.strftime("completeness_report_%Y%m%d_%H%M%S.xlsx"))
        
        # make path usable directly in windows
        report_path = report_path.replace('/', '\\')
        
        main(application, report_path, previously_unanalysed=load_previously_unanalysed_files(self.get_plugin().intermediate))
        
        logging.info("Generated report %s" % report_path)
        logging.info("##################################################################")
