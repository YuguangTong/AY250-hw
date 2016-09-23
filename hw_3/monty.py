import speech_recognition as sr
import time

class Monty(object):
    """
    Monty is a Siri-like program with the following properties:
        - take voice command and parse using GOOGLE SPEECH RECOGNITION service.
        - take three different types of actions:
            -- send an email to yourself
            -- do some math
            -- tell a joke
            
    example 1: if you say "Monty: email me with subject hello and body goodbye", 
        it will email you with the appropriate subject and body.
        
    example 2: If you say "Monty: tell me a joke" then it will go to the web 
        and find a joke and print it for you.
    
    example 3: If you say, "Monty: calculate two times three" it should response 
        with printing the number 6.
    """
    
    def __init__(self, monty_gmail_username, 
                 monty_gmail_password, user_email):
        self.gmail_username = monty_gmail_username
        self.gmail_password = monty_gmail_password
        self.user_email = user_email
    

    def ask(self):
        """
        Ask Monty
        Monty will prompt user to speak and respond
        """
        
        # obtain audio from the microphone
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Monty: Say something!")
            time.sleep(0.05)
            audio = r.listen(source) 
            
        # recognize speech using Google Speech Recognition
        try:
            # using the default API key in 
            transcript = r.recognize_google(audio)
            self.transcript = transcript
            print("Monty: I thinks you said")
            print('\t' + transcript)
        except sr.UnknownValueError:
            print("Monty: I could not understand audio")
            time.sleep(0.05)
            print("Monty: Please ask me again")
        except sr.RequestError as e:
            print("Monty could not request results" + 
                  "from Google Speech Recognition service; {0}".format(e))
            import sys
            sys.exit("cannot reach to Google Speech Recognition")
            
        # analyze transcript
        if self.has_math(transcript):
            self.do_math(transcript)
            
        elif self.has_joke(transcript):
            self.tell_joke()
            
        elif self.has_email(transcript):
            msg = self.construct_email_msg(self.gmail_username, 
                                           self.user_email, transcript)
            self.send_email(self.gmail_username, self.user_email, 
                            self.gmail_password, msg)
            
        else:
            print("Monty: sorry, I dont know what to do now.")
        
    def has_math(self, transcript):
        """
        Check if Audio instruction contains any math
        """
        math_operators = ['+', '-', 'times', 'multiplied', 'divide']
        for op in math_operators:
            if op in transcript:
                return True
        return False

    def has_email(self, transcript):
        """
        Check if audio instruction contains email request
        """
        return 'email' in transcript

    def has_joke(self, transcript):
        """
        check if audio instruction contains request about jokes
        """
        return 'joke' in transcript


    def tell_joke(self):
        """
        Open on browser a webpage with jokes
        """
        print("Monty: Okay, I will find a joke for you.")
        time.sleep(0.1)
        
        import webbrowser
        joke_url = 'http://www.short-funny.com'
        webbrowser.open(joke_url)

    def do_math(self, transcript):
        """
        Do simple math and output result
        Can only deal with arithmetic in one of the following form:
        - <num> + <num>
        - <num> - <num>
        - <num> divided by <num>
        - <num> times <num>
        - <num> multiplied by <num>

        Use regular expression to extract 
        """
        print("Monty: Okay, I will do some math for you.")
        time.sleep(0.1)
        import re

        pattern = r'.*?\s*(?P<a>[0-9]+)\s*(?P<op>[-+]|divided by|times|multiplied by)\s*(?P<b>[0-9]+)$'
        matched = re.match(pattern, transcript)

        if matched:
            math_dict = matched.groupdict()
            a = math_dict['a']
            b = math_dict['b']
            op = math_dict['op']
            if op == '+':
                result = int(a) + int(b)
            elif op == '-':
                result = int(a) - int(b)
            elif op == 'divided by':
                try:
                    result = int(a) / int(b)
                except ZeroDivisionError as e:
                    result = 'infinity'
            elif op == 'times' or op == 'multiplied by':
                result = int(a) * int(b)
            print('Monty: ' + a + ' ' + op + ' ' + b  + ' = ' + str(result))

        else:
            print('Monty dont understand the math question that you asked')  

            
    def send_email(self, fromaddr, toaddr, password, msg):
        """
        log into Monty's gmail (FROMADDR) and send msg to TOADDR

        Paramarater
        -----------
            fromaddr: string, single gmail address
            toaddr: string, any single email address
            msg: an email.MIMEMultipart object

        """
        import smtplib 

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(fromaddr, password)
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()

    def construct_email_msg(self, fromaddr, toaddr, transcript):
        """
        construct email msg from the audio transcript.
        Can identify: subject, body, 

        Paramarater
        -----------
            fromaddr: string, single gmail address
            toaddr: string, any single email address
            transcript: string containing instructions to
                construct email

        """
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr

        # assume short sentence ...
        tokens = transcript.split(' ')

        # default subject and body
        subj = "email from Monty"
        bdy = "Monty says hello!"

        # modify subject/body if user specifies
        n = len(tokens)
        for i, token in enumerate(tokens):
            if token == 'subject' and i < n-1:
                subj = tokens[i+1]
            if token == 'body' and i < n-1:
                bdy = tokens[i+1]

        msg['Subject'] = subj
        body = bdy
        msg.attach(MIMEText(body, 'plain'))
    
        return msg    
