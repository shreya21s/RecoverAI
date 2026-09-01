import random
from datetime import datetime, timedelta

def generate_synthetic_data():
    """
    Generates a deterministic synthetic dataset of customers, payments, and recovery cases.
    Returns:
        tuple: (customers, payments, recovery_cases)
    """
    # Fix seed for strict determinism
    random.seed(42)

    # 1. Generate 50 Customers
    customers = []
    
    # Showcase customers
    showcase_customers = [
        {
            "customer_id": "CUST-DEMO-001",
            "name": "Aarav Sharma",
            "segment": "HIGH_VALUE_RELIABLE",
            "lifetime_value": 150000.0,
            "total_successful_payments": 25,
            "total_failed_payments": 1,
            "average_payment_amount": 6000.0,
            "engagement_score": 9.5
        },
        {
            "customer_id": "CUST-DEMO-002",
            "name": "Ishaan Patel",
            "segment": "AVERAGE",
            "lifetime_value": 45000.0,
            "total_successful_payments": 18,
            "total_failed_payments": 2,
            "average_payment_amount": 2500.0,
            "engagement_score": 7.0
        },
        {
            "customer_id": "CUST-DEMO-003",
            "name": "Priya Nair",
            "segment": "AT_RISK",
            "lifetime_value": 95000.0,
            "total_successful_payments": 5,
            "total_failed_payments": 4,
            "average_payment_amount": 19000.0,
            "engagement_score": 4.5
        },
        {
            "customer_id": "CUST-DEMO-004",
            "name": "Aditya Verma",
            "segment": "LOW_ENGAGEMENT",
            "lifetime_value": 15000.0,
            "total_successful_payments": 3,
            "total_failed_payments": 5,
            "average_payment_amount": 5000.0,
            "engagement_score": 2.0
        },
        {
            "customer_id": "CUST-DEMO-005",
            "name": "Ananya Reddy",
            "segment": "AT_RISK",
            "lifetime_value": 60000.0,
            "total_successful_payments": 8,
            "total_failed_payments": 3,
            "average_payment_amount": 7500.0,
            "engagement_score": 5.0
        }
    ]
    customers.extend(showcase_customers)

    first_names = [
        "Rohan", "Siddharth", "Rahul", "Amit", "Vikram", "Karan", "Arjun", "Kabir", "Vijay", "Sanjay",
        "Neha", "Deepika", "Kriti", "Shruti", "Riya", "Aditi", "Meera", "Pooja", "Divya", "Sanya",
        "Abhishek", "Sunil", "Rajesh", "Manish", "Anil", "Harish", "Vivek", "Sandeep", "Alok", "Sameer",
        "Ritu", "Shalini", "Preeti", "Komal", "Swati", "Rashmi", "Jyoti", "Nisha", "Kiran", "Geeta",
        "Dev", "Yash", "Nikhil", "Pranav", "Varun"
    ]
    last_names = [
        "Kumar", "Singh", "Joshi", "Gupta", "Mehta", "Sen", "Roy", "Bose", "Dutta", "Das", "Iyer",
        "Rao", "Nair", "Sharma", "Reddy", "Patel", "Verma", "Choudhury", "Pillai", "Mishra"
    ]
    segments = ["HIGH_VALUE_RELIABLE", "RELIABLE", "AVERAGE", "AT_RISK", "LOW_ENGAGEMENT"]

    for i in range(6, 51):
        cust_id = f"CUST-{i:03d}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        segment = random.choices(
            segments,
            weights=[0.15, 0.25, 0.35, 0.15, 0.10],
            k=1
        )[0]

        if segment == "HIGH_VALUE_RELIABLE":
            success = random.randint(20, 50)
            failed = random.randint(0, 2)
            avg_amt = float(random.randint(5000, 15000))
            ltv = float(success * avg_amt)
            engagement = round(random.uniform(8.5, 10.0), 1)
        elif segment == "RELIABLE":
            success = random.randint(10, 25)
            failed = random.randint(0, 3)
            avg_amt = float(random.randint(3000, 8000))
            ltv = float(success * avg_amt)
            engagement = round(random.uniform(7.0, 8.5), 1)
        elif segment == "AVERAGE":
            success = random.randint(5, 15)
            failed = random.randint(1, 4)
            avg_amt = float(random.randint(2000, 5000))
            ltv = float(success * avg_amt)
            engagement = round(random.uniform(5.0, 7.0), 1)
        elif segment == "AT_RISK":
            success = random.randint(2, 8)
            failed = random.randint(3, 8)
            avg_amt = float(random.randint(1500, 4000))
            ltv = float(success * avg_amt)
            engagement = round(random.uniform(3.0, 5.0), 1)
        else: # LOW_ENGAGEMENT
            success = random.randint(0, 3)
            failed = random.randint(4, 10)
            avg_amt = float(random.randint(1000, 3000))
            ltv = float(success * avg_amt)
            engagement = round(random.uniform(1.0, 3.0), 1)

        customers.append({
            "customer_id": cust_id,
            "name": name,
            "segment": segment,
            "lifetime_value": ltv,
            "total_successful_payments": success,
            "total_failed_payments": failed,
            "average_payment_amount": avg_amt,
            "engagement_score": engagement
        })

    # Helper function to find customers matching segments
    def get_customers_by_segments(segs):
        return [c for c in customers if c["segment"] in segs]

    # 2. Define Showcase Cases
    showcases = [
        # SHOWCASE 1: Easy Recovery (Temporary Bank Failure)
        {
            "case_id": "REC-DEMO-001",
            "payment_id": "PAY-DEMO-001",
            "customer_id": "CUST-DEMO-001",
            "amount": 4500.0,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "FAILED",
            "failure_code": "TEMPORARY_BANK_FAILURE",
            "retry_count": 0,
            "reminder_count": 0,
            "is_disputed": False,
            "is_recovered": False,
            "case_status": "PENDING",
            "requires_approval": False,
            "metadata_json": {
                "expected_outcome": "SUCCESS",
                "expected_strategy": "SMART_RETRY",
                "recovered_amount": 4500.0,
                "scenario_name": "Showcase 1: Easy Recovery (Temporary Failure)"
            }
        },
        # SHOWCASE 2: Payment Abandonment
        {
            "case_id": "REC-DEMO-002",
            "payment_id": "PAY-DEMO-002",
            "customer_id": "CUST-DEMO-002",
            "amount": 2500.0,
            "currency": "INR",
            "payment_method": "CARD",
            "status": "FAILED",
            "failure_code": "PAYMENT_ABANDONED",
            "retry_count": 0,
            "reminder_count": 0,
            "is_disputed": False,
            "is_recovered": False,
            "case_status": "PENDING",
            "requires_approval": False,
            "metadata_json": {
                "expected_outcome": "SUCCESS",
                "expected_strategy": "SEND_PAYMENT_LINK",
                "recovered_amount": 2500.0,
                "scenario_name": "Showcase 2: Payment Abandonment"
            }
        },
        # SHOWCASE 3: High-Value HITL
        {
            "case_id": "REC-DEMO-003",
            "payment_id": "PAY-DEMO-003",
            "customer_id": "CUST-DEMO-003",
            "amount": 75000.0,
            "currency": "INR",
            "payment_method": "NETBANKING",
            "status": "FAILED",
            "failure_code": "UNKNOWN_FAILURE",
            "retry_count": 1,
            "reminder_count": 1,
            "is_disputed": False,
            "is_recovered": False,
            "case_status": "PENDING",
            "requires_approval": True,
            "metadata_json": {
                "expected_outcome": "REQUIRES_APPROVAL",
                "expected_strategy": "ESCALATE_TO_HUMAN",
                "recovered_amount": 0.0,
                "scenario_name": "Showcase 3: High-Value HITL Required"
            }
        },
        # SHOWCASE 4: Policy Stop
        {
            "case_id": "REC-DEMO-004",
            "payment_id": "PAY-DEMO-004",
            "customer_id": "CUST-DEMO-004",
            "amount": 5000.0,
            "currency": "INR",
            "payment_method": "CARD",
            "status": "FAILED",
            "failure_code": "REPEATED_FAILURE",
            "retry_count": 3,
            "reminder_count": 3,
            "is_disputed": False,
            "is_recovered": False,
            "case_status": "PENDING",
            "requires_approval": False,
            "metadata_json": {
                "expected_outcome": "STOPPED_BY_POLICY",
                "expected_strategy": "STOP_RECOVERY",
                "recovered_amount": 0.0,
                "scenario_name": "Showcase 4: Repeated Failures Policy Stop"
            }
        },
        # SHOWCASE 5: Customer Dispute
        {
            "case_id": "REC-DEMO-005",
            "payment_id": "PAY-DEMO-005",
            "customer_id": "CUST-DEMO-005",
            "amount": 12000.0,
            "currency": "INR",
            "payment_method": "CARD",
            "status": "FAILED",
            "failure_code": "AUTHENTICATION_FAILED",
            "retry_count": 1,
            "reminder_count": 0,
            "is_disputed": True,
            "is_recovered": False,
            "case_status": "PENDING",
            "requires_approval": False,
            "metadata_json": {
                "expected_outcome": "STOPPED_BY_POLICY",
                "expected_strategy": "ESCALATE_TO_HUMAN",
                "recovered_amount": 0.0,
                "scenario_name": "Showcase 5: Disputed Charge Stop"
            }
        }
    ]

    payments = []
    recovery_cases = []

    # Helper to add showcase records
    for s in showcases:
        payments.append({
            "payment_id": s["payment_id"],
            "customer_id": s["customer_id"],
            "amount": s["amount"],
            "currency": s["currency"],
            "payment_method": s["payment_method"],
            "status": s["status"],
            "failure_code": s["failure_code"],
            "retry_count": s["retry_count"],
            "reminder_count": s["reminder_count"],
            "is_disputed": s["is_disputed"],
            "is_recovered": s["is_recovered"],
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 10))
        })
        recovery_cases.append({
            "case_id": s["case_id"],
            "payment_id": s["payment_id"],
            "batch_id": "BATCH-2026-DEMO-001",
            "status": s["case_status"],
            "current_strategy": None,
            "recovery_probability": 0.0,
            "expected_recovery_value": 0.0,
            "estimated_action_cost": 0.0,
            "requires_human_approval": s["requires_approval"],
            "metadata_json": s["metadata_json"]
        })

    # 3. Generate Remaining 95 Cases (to total exactly 100 cases)
    # Target counts per category:
    # A (Temporary Failure): 20 total (1 showcase + 19 generated)
    # B (Insufficient Funds): 20 total (0 showcase + 20 generated)
    # C (Payment Abandonment): 15 total (1 showcase + 14 generated)
    # D (Payment Method Issue): 10 total (0 showcase + 10 generated)
    # E (High-Value Cases): 10 total (1 showcase + 9 generated)
    # F (Repeated Failure): 12 total (1 showcase + 11 generated)
    # G (Customer Dispute): 5 total (1 showcase + 4 generated)
    # H (Already Recovered): 8 total (0 showcase + 8 generated)

    category_targets = {
        "A": 19,
        "B": 20,
        "C": 14,
        "D": 10,
        "E": 9,
        "F": 11,
        "G": 4,
        "H": 8
    }

    base_case_index = 1
    base_pay_index = 1

    for category, count in category_targets.items():
        for _ in range(count):
            case_id = f"REC-{base_case_index:03d}"
            payment_id = f"PAY-{base_pay_index:03d}"
            base_case_index += 1
            base_pay_index += 1

            amount = float(random.randint(1000, 15000))
            currency = "INR"
            payment_method = random.choice(["CARD", "UPI", "NETBANKING", "WALLET"])
            status = "FAILED"
            failure_code = None
            retry_count = 0
            reminder_count = 0
            is_disputed = False
            is_recovered = False
            case_status = "PENDING"
            requires_human_approval = False
            expected_outcome = "SUCCESS"
            expected_strategy = "SMART_RETRY"
            recovered_amount = 0.0

            if category == "A":
                # Temporary Failures: Strong segment, low retry
                cust = random.choice(get_customers_by_segments(["HIGH_VALUE_RELIABLE", "RELIABLE"]))
                failure_code = random.choice(["TEMPORARY_BANK_FAILURE", "NETWORK_ERROR", "TEMPORARY_DECLINE"])
                expected_outcome = "SUCCESS"
                expected_strategy = "SMART_RETRY"
                recovered_amount = amount
            
            elif category == "B":
                # Insufficient Funds: various segments, some fail, some pass
                cust = random.choice(get_customers_by_segments(["RELIABLE", "AVERAGE", "AT_RISK"]))
                failure_code = "INSUFFICIENT_FUNDS"
                retry_count = random.randint(0, 1)
                if cust["segment"] in ["RELIABLE", "AVERAGE"]:
                    expected_outcome = "SUCCESS"
                    expected_strategy = "WAIT_AND_RETRY"
                    recovered_amount = amount
                else:
                    expected_outcome = "FAILED"
                    expected_strategy = "SEND_REMINDER"
                    recovered_amount = 0.0

            elif category == "C":
                # Payment Abandonment: no error, average engagement
                cust = random.choice(get_customers_by_segments(["AVERAGE", "RELIABLE"]))
                failure_code = "PAYMENT_ABANDONED"
                expected_outcome = "SUCCESS"
                expected_strategy = "SEND_PAYMENT_LINK"
                recovered_amount = amount

            elif category == "D":
                # Payment Method Issue: Expired/Invalid method
                cust = random.choice(get_customers_by_segments(["AVERAGE", "HIGH_VALUE_RELIABLE", "RELIABLE"]))
                failure_code = random.choice(["EXPIRED_PAYMENT_METHOD", "INVALID_PAYMENT_METHOD", "AUTHENTICATION_FAILED"])
                expected_outcome = "SUCCESS"
                expected_strategy = "OFFER_ALTERNATIVE_PAYMENT_METHOD"
                recovered_amount = amount

            elif category == "E":
                # High Value: 50,000 - 150,000
                cust = random.choice(get_customers_by_segments(["HIGH_VALUE_RELIABLE", "RELIABLE", "AT_RISK"]))
                amount = float(random.randint(50000, 150000))
                failure_code = random.choice(["UNKNOWN_FAILURE", "AUTHENTICATION_FAILED", "TEMPORARY_BANK_FAILURE"])
                
                # High-value triggers HITL if segment is AT_RISK or unknown failure
                if cust["segment"] == "AT_RISK" or failure_code == "UNKNOWN_FAILURE":
                    requires_human_approval = True
                    expected_outcome = "REQUIRES_APPROVAL"
                    expected_strategy = "ESCALATE_TO_HUMAN"
                    recovered_amount = 0.0
                else:
                    expected_outcome = "SUCCESS"
                    expected_strategy = "SMART_RETRY"
                    recovered_amount = amount

            elif category == "F":
                # Repeated Failures: low engagement, high retry/reminder
                cust = random.choice(get_customers_by_segments(["LOW_ENGAGEMENT", "AT_RISK"]))
                failure_code = "REPEATED_FAILURE"
                retry_count = random.randint(2, 4)
                reminder_count = random.randint(2, 4)
                expected_outcome = "STOPPED_BY_POLICY"
                expected_strategy = "STOP_RECOVERY"
                recovered_amount = 0.0

            elif category == "G":
                # Customer Dispute
                cust = random.choice(get_customers_by_segments(["AVERAGE", "AT_RISK"]))
                failure_code = "AUTHENTICATION_FAILED"
                is_disputed = True
                expected_outcome = "STOPPED_BY_POLICY"
                expected_strategy = "ESCALATE_TO_HUMAN"
                recovered_amount = 0.0

            elif category == "H":
                # Already Recovered / Terminal
                cust = random.choice(get_customers_by_segments(["HIGH_VALUE_RELIABLE", "RELIABLE", "AVERAGE"]))
                failure_code = random.choice(["TEMPORARY_BANK_FAILURE", "INSUFFICIENT_FUNDS"])
                status = "RECOVERED"
                is_recovered = True
                case_status = "RECOVERED"
                expected_outcome = "SUCCESS"
                expected_strategy = "SMART_RETRY"
                recovered_amount = amount

            # Append the generated items
            payments.append({
                "payment_id": payment_id,
                "customer_id": cust["customer_id"],
                "amount": amount,
                "currency": currency,
                "payment_method": payment_method,
                "status": status,
                "failure_code": failure_code,
                "retry_count": retry_count,
                "reminder_count": reminder_count,
                "is_disputed": is_disputed,
                "is_recovered": is_recovered,
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 10))
            })

            recovery_cases.append({
                "case_id": case_id,
                "payment_id": payment_id,
                "batch_id": "BATCH-2026-DEMO-001",
                "status": case_status,
                "current_strategy": None,
                "recovery_probability": 0.0,
                "expected_recovery_value": 0.0,
                "estimated_action_cost": 0.0,
                "requires_human_approval": requires_human_approval,
                "metadata_json": {
                    "expected_outcome": expected_outcome,
                    "expected_strategy": expected_strategy,
                    "recovered_amount": recovered_amount,
                    "category": category
                }
            })

    return customers, payments, recovery_cases
