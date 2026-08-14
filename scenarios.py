SCENARIOS = [
    {
        "id": "appointment_simple",
        "name": "Simple Appointment Scheduling",
        "context": "You are Alex Johnson. You need to schedule a routine check-up with Dr. Smith. Prefer weekday mornings.",
        "goal": "Schedule a routine check-up appointment with Dr. Smith for next week.",
        "initial_message": "Hi, I'd like to schedule a routine check-up with Dr. Smith please."
    },
    {
        "id": "appointment_reschedule",
        "name": "Rescheduling Appointment",
        "context": "You are Jordan Lee. You have an appointment this Friday at 2pm with Dr. Smith that you need to reschedule to next Tuesday.",
        "goal": "Reschedule your Friday 2pm appointment to next Tuesday.",
        "initial_message": "Hi, I need to reschedule my appointment this Friday at 2pm with Dr. Smith."
    },
    {
        "id": "appointment_cancel",
        "name": "Canceling Appointment",
        "context": "You are Casey Morgan. You have an appointment tomorrow at 10am with Dr. Smith but need to cancel due to a conflict.",
        "goal": "Cancel your appointment tomorrow at 10am with Dr. Smith.",
        "initial_message": "Hi, I need to cancel my appointment tomorrow at 10am with Dr. Smith please."
    },
    {
        "id": "refill_request",
        "name": "Medication Refill",
        "context": "You are Taylor Brooks. You take Lisinopril 10mg daily and need a refill. Your last prescription was filled 25 days ago.",
        "goal": "Request a refill for Lisinopril 10mg.",
        "initial_message": "Hi, I need a refill on my Lisinopril 10mg prescription please."
    },
    {
        "id": "office_hours",
        "name": "Office Hours Inquiry",
        "context": "You are Avery Chen. You want to know the office hours, location, and whether they accept your new insurance (BlueCross BlueShield).",
        "goal": "Find out office hours, location, and insurance acceptance.",
        "initial_message": "Hi, I'm new to the area. Can you tell me your office hours and location? Also, do you accept BlueCross BlueShield?"
    },
    {
        "id": "insurance_question",
        "name": "Insurance Verification",
        "context": "You are Riley Patel. You have Aetna insurance and want to verify it's accepted before your visit.",
        "goal": "Verify that Aetna insurance is accepted.",
        "initial_message": "Hi, I have Aetna insurance. Can you verify that you accept it?"
    },
    {
        "id": "prescription_question",
        "name": "Prescription Question",
        "context": "You are Quinn Garcia. You were prescribed Amoxicillin and want to know if you should take it with food.",
        "goal": "Ask about taking Amoxicillin with food.",
        "initial_message": "Hi, I was prescribed Amoxicillin. Should I take it with food?"
    },
    {
        "id": "billing_question",
        "name": "Billing Inquiry",
        "context": "You are Cameron Diaz (no relation to the actress). You received a bill for $150 and want to know what it's for.",
        "goal": "Inquire about a $150 bill you received.",
        "initial_message": "Hi, I got a bill for $150 and I'm not sure what it's for. Can you help me understand?"
    },
    {
        "id": "barge_in_test",
        "name": "Interruption/Barge-in Test",
        "context": "You are Drew Wilson. You want to test if the agent handles interruptions. Start speaking and then interrupt yourself mid-sentence.",
        "goal": "Test the agent's ability to handle interruptions and barge-in scenarios.",
        "initial_message": "Hi, I was wondering if I could maybe no wait, actually, can I just schedule a check-up?"
    },
    {
        "id": "unclear_request",
        "name": "Unclear Request Test",
        "context": "You are Sam Rivera. You give vague, unclear requests to test if the agent can ask clarifying questions.",
        "goal": "Test the agent's ability to handle unclear or vague requests.",
        "initial_message": "Uh, I think I need something. Can you help me with that thing?"
    },
    {
        "id": "weekend_appointment",
        "name": "Weekend Appointment Edge Case",
        "context": "You are Jamie Foster. You ask for a Sunday appointment to test if the agent knows the practice is closed on weekends.",
        "goal": "Test if the agent correctly identifies that the practice is closed on weekends.",
        "initial_message": "Hi, can I come in on Sunday at 10am for an appointment?"
    },
    {
        "id": "multiple_requests",
        "name": "Multiple Requests",
        "context": "You are Alex Johnson again. You want to both reschedule an appointment and request a refill in the same call.",
        "goal": "Handle multiple requests in a single call.",
        "initial_message": "Hi, I need to reschedule my appointment to next week and also get a refill on my medication."
    }
]
