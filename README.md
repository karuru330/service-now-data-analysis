
This Data pipeline is to retrieve the data from service-now based on the requirements specified in config file and ingest the data into data lake. Further the data will be used by LLM to answer prompts.

Architecture Diagram:

![Architecture Diagram](service-now-data-analysis/Architecture Diagram.png)

Step 1: Create service-now developer account

**Go to the Developer Portal**  
   Visit the [ServiceNow Developer Site](https://developer.servicenow.com/).

**Click “Sign Up”**  
   - You’ll find this at the top-right corner.
   - Fill in your **name**, **email**, **country**, and **password**.
   - Complete the **CAPTCHA** and agree to the terms.

**Verify Your Email**  
   - Check your inbox (and spam folder) for a verification email.
   - Click the link to activate your account.

**Log In and Request a Personal Developer Instance**  
   - After logging in, click **“Request Instance”**.
   - Choose a version (latest is fine) and wait a few minutes for it to be provisioned.
   - You’ll get a unique URL like `https://dev12345.service-now.com`.

![alt text](<Architecture Diagram.png>)