## Context: 
Lending companies require a system where the field collections team and the central calling team can update and access customer interactions centrally. 
## Problem: 
There is no single system where both teams can track customer communication. The field team updates are not accessible to the calling team in real-time, and vice versa. 
## Objective: 
To build a backend system in Django that allows..: 
- Both—the field collections team and central calling team to update customer interactions in a centrally accessible system.
- Users to have access to prior communication history—callers before making a call and collection officers before visiting a customer.
- Each customer to be assigned to specific collection officers in the system. Only the assigned collection officer, along with their managers and super managers, should be able to update customer communication in the system. Whereas, any calling agent can contact any customer and log updates.
- The system should maintain a complete conversation history with a disposition assigned to each interaction. The latest disposition of every customer should be made visible to the users (both) at the front, on the UI. 
- Every customer interaction record can have - a comment, a disposition, the timestamp, next call date (if the customer asks for), etc. (Feel free to add your own fields which you think will be helpful).  
## Requirements: 
- System:
	- [ ]  Design the backend using Django, including necessary models, database structures, and APIs. Use a PostgreSQL or a MySQL database. 
	- [ ] Implement a hierarchy for collection officers, managers, and super managers. Only assigned collection officers (and their seniors) should be able modify, add, or record customer interactions, while any calling agents can update any customer. (Utilize a suitable Python package for hierarchy management, if you want to).
	- [ ] Maintain full conversation history with disposition tracking for all customer interactions from both the field and calling teams. 
- Functionalities: 
	- [ ] The logs of all user actions should be recorded and made available.
	- [ ] Option to bulk onboard new customers, field team (collection agents and seniors), calling team — with a CSV import (even just on the Django admin will work.) Auto credential creation, when a user is created, set a random password.
	- [ ] Option to bulk upload and record Comments and Dispositions for all the customers—as a new latest entry.
	- [ ] Think, design & implement all the APIs that’ll be needed to build the app. Log all API request-response logs. Evaluate all the different parameters in detail, which you think will be required, in all the different APIs.
	- [ ] A filter that'll allow the users to filter all customers based on the latest disposition.
	- [ ] APIs:
		- [ ] To record a new conversation update from the field team.
		- [ ] To record a new conversation update from the calling team.
		- [ ] To display all the customers data to the field team/collection officers (based on customers allocated) and to the calling team (all).
		- [ ] To support the bulk upload functionality requirements.
		- [ ] And more that you can think of..  
## Notes: 
- Your ability to think (and even ask questions) to understand the product and the usability better - will be valued. 
- Assume hierarchy up to 3 layers only. Make other necessary assumptions (like disposition options) and choose the best approach for implementation.
- Handle errors gracefully.
- Reach out for any clarifications on the problem statement or implementation.