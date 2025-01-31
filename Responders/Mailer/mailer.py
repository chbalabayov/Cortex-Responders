#!/usr/bin/env python
# encoding: utf-8

from cortexutils.responder import Responder
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from email.utils import make_msgid
import time

class Mailer(Responder):
    def __init__(self):
        Responder.__init__(self)
        self.smtp_host = self.get_param('config.smtp_host', None, 'missing smtp host')
        self.smtp_port = self.get_param('config.smtp_port', None, 'Missing smtp port')
        self.mail_from = self.get_param('config.from', None, 'Missing sender email address')
        self.smtp_auth = self.get_param('config.smtp_auth', None)
        self.mail_user = self.get_param('config.smtp_user', None, 'Missing auth user')
        self.mail_pass = self.get_param('config.smtp_pass', None, 'Missing auth pass')

    def run(self):
        Responder.run(self)

        title = self.get_param('data.title', None, 'Title is missing')
        title = title.encode('utf-8')

	description = "This is an email alert from TheHive as a new case has been added for investigation. Please read all the details below." 
	description += "\n----------------------------------------------------------------------------------------------------------------------"
	description += "\n\nCase description:\n" + self.get_param('data.description', None, 'Description is missing')
	#description = self.get_param('data.customFields', None, 'Dashboard name is not specified')	
	description += "\n\nEvent time: " + str(time.strftime('%d.%m.%Y %H:%M', time.localtime(self.get_param('data.startDate') / 1000)))
	description += "\nDashboard name: " + self.get_param('data.customFields.dashboard-name.string', None, 'Dashboard name is not specified')
	description += "\nEvent count: " + str(self.get_param('data.customFields.event-count.integer', None, 'Event count is not specified'))
	description += "\nEvent name: " + self.get_param('data.customFields.event-name.string', None, 'Event name is not specified')
	description += "\nSource IP: " + self.get_param('data.customFields.source-ip.string', None, 'Source IP is not specified')
	description += "\nSource port: " + self.get_param('data.customFields.source-port.string', None, 'Source port is not specified')
	description += "\nSource organization name: " + self.get_param('data.customFields.source-org-name.string', None, 'Source organization name is not specified')
	description += "\nSource country: " + self.get_param('data.customFields.source-country.string', None, 'Source country is not specified')
	try:	
		description += "\nUsername: " + self.get_param('data.customFields.username.string', None)
	except:
		description += "\nUsername: username is undefined"
	description += "\nDestination IP: " + self.get_param('data.customFields.destination-ip.string', None, 'Destination IP is not specified')
	description += "\nDestination port: " + self.get_param('data.customFields.destination-port.string', None, 'Destination port is not specified')
	description += "\nDestination country: " + self.get_param('data.customFields.destination-country.string', None, 'Destination country is not specified')
	description += "\nFLD: " + self.get_param('data.customFields.fld.string', None, 'FLD is not specified')
        #description = self.get_param('data', None, 'None')
	#description = json.dumps(description)
	description = description.encode('utf-8')

        mail_to = None
        if self.data_type == 'thehive:case':
            # Search recipient address in tags
            tags = self.get_param('data.tags', None, 'recipient address not found in tags')

            mail_tags = [t[5:] for t in tags if t.startswith('mail:')]
            if mail_tags:
                mail_to = mail_tags.pop()
            else:
                self.error('recipient address not found in observables')
        elif self.data_type == 'thehive:alert':
            # Search recipient address in artifacts
            artifacts = self.get_param('data.artifacts', None, 'recipient address not found in observables')
            mail_artifacts = [a['data'] for a in artifacts if a.get('dataType') == 'mail' and 'data' in a]
            if mail_artifacts:
                mail_to = mail_artifacts.pop()
            else:
                self.error('recipient address not found in observables')
        else:
            self.error('Invalid dataType')

        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = self.mail_from
        msg['To'] = mail_to
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()
        msg.attach(MIMEText(description))
        
        
        s = smtplib.SMTP(self.smtp_host, self.smtp_port)

        if(self.smtp_auth):
            try:
                s.starttls()
                s.login(self.mail_user,self.mail_pass)
            except:
                self.error('an error occured with SMTP username/password')
            
        try:
            s.sendmail(self.mail_from, [mail_to], msg.as_string())
            s.quit()
            self.report({'message': 'message sent'})
        except:
            self.error('unable to send email')

    def operations(self, raw):
        return [self.build_operation('AddTagToCase', tag='Mail sent')]


if __name__ == '__main__':
    Mailer().run()
