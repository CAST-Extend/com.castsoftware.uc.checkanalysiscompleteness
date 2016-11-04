import cast_upgrade_1_5_1 # @UnusedImport
from cast.application import ApplicationLevelExtension
import logging
import xlsxwriter
import unanalysed
import os


class CheckApplication(ApplicationLevelExtension):

    def end_application(self, application):
        
        logging.info("##################################################################")
        logging.info("Checking application completeness")
        
        report_path = os.path.join(self.get_plugin().intermediate, 'completeness_report.xlsx')
        
        workbook = xlsxwriter.Workbook(report_path)
        unanalysed.generate_report(application, workbook)
        workbook.close()
        
        logging.info("Generated report %s" % report_path)
        logging.info("##################################################################")
