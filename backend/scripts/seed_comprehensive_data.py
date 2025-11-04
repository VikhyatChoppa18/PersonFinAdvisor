"""
Comprehensive script to seed realistic dummy data for testing.
"""
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from app.db.database import SessionLocal
from app.db import models
from app.core.security import get_password_hash

def seed_comprehensive_data():
    """Seed comprehensive realistic dummy data."""
    db = SessionLocal()
    try:
        # Get or create test user
        user = db.query(models.User).filter(models.User.email == "test@example.com").first()
        
        if not user:
            print("Creating test user...")
            user = models.User(
                email="test@example.com",
                hashed_password=get_password_hash("testpass123"),
                full_name="Test User",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created user: {user.email}")
        else:
            print(f"✅ Found user: {user.email}")
        
        # Delete existing data to start fresh
        db.query(models.Transaction).filter(models.Transaction.user_id == user.id).delete()
        db.query(models.Budget).filter(models.Budget.user_id == user.id).delete()
        db.query(models.Goal).filter(models.Goal.user_id == user.id).delete()
        db.query(models.Account).filter(models.Account.user_id == user.id).delete()
        db.commit()
        
        # Create multiple accounts
        accounts_data = [
            {"name": "Primary Checking", "type": "checking", "balance": 8500.00},
            {"name": "Savings Account", "type": "savings", "balance": 15000.00},
            {"name": "Credit Card", "type": "credit", "balance": -1200.00},
        ]
        
        accounts = []
        for acc_data in accounts_data:
            account = models.Account(
                user_id=user.id,
                account_id=f"acc_{user.id}_{acc_data['type']}_{len(accounts)}",
                name=acc_data["name"],
                type=acc_data["type"],
                balance=acc_data["balance"],
                currency="USD",
                is_active=True
            )
            db.add(account)
            accounts.append(account)
        
        db.commit()
        print(f"✅ Created {len(accounts)} accounts")
        
        # Create comprehensive budgets with realistic spending
        now = datetime.now()
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        budgets_data = [
            {"category": "Food & Dining", "amount": 600.00, "spent_pct": 0.72},
            {"category": "Shopping", "amount": 400.00, "spent_pct": 0.65},
            {"category": "Transportation", "amount": 350.00, "spent_pct": 0.80},
            {"category": "Bills & Utilities", "amount": 450.00, "spent_pct": 1.0},
            {"category": "Entertainment", "amount": 200.00, "spent_pct": 0.55},
            {"category": "Healthcare", "amount": 150.00, "spent_pct": 0.40},
            {"category": "Education", "amount": 300.00, "spent_pct": 0.30},
            {"category": "Travel", "amount": 500.00, "spent_pct": 0.25},
            {"category": "Home & Garden", "amount": 250.00, "spent_pct": 0.60},
            {"category": "Personal Care", "amount": 180.00, "spent_pct": 0.70},
        ]
        
        for budget_data in budgets_data:
            budget = models.Budget(
                user_id=user.id,
                category=budget_data["category"],
                amount=budget_data["amount"],
                current_spent=budget_data["amount"] * budget_data["spent_pct"],
                period="monthly",
                start_date=start_date,
                end_date=end_date,
                is_active=True,
            )
            db.add(budget)
        
        db.commit()
        print(f"✅ Created {len(budgets_data)} budgets")
        
        # Create comprehensive goals
        goals_data = [
            {
                "name": "Emergency Fund",
                "target_amount": 15000.00,
                "current_amount": 5200.00,
                "target_date": now + timedelta(days=180),
                "goal_type": "savings"
            },
            {
                "name": "Vacation to Europe",
                "target_amount": 5000.00,
                "current_amount": 2100.00,
                "target_date": now + timedelta(days=150),
                "goal_type": "savings"
            },
            {
                "name": "New Car Down Payment",
                "target_amount": 8000.00,
                "current_amount": 1200.00,
                "target_date": now + timedelta(days=365),
                "goal_type": "savings"
            },
            {
                "name": "Investment Portfolio",
                "target_amount": 20000.00,
                "current_amount": 8500.00,
                "target_date": now + timedelta(days=730),
                "goal_type": "investment"
            },
            {
                "name": "Pay Off Credit Card",
                "target_amount": 5000.00,
                "current_amount": 3800.00,
                "target_date": now + timedelta(days=90),
                "goal_type": "debt_payoff"
            },
            {
                "name": "Home Down Payment",
                "target_amount": 50000.00,
                "current_amount": 15000.00,
                "target_date": now + timedelta(days=1095),
                "goal_type": "savings"
            },
        ]
        
        for goal_data in goals_data:
            goal = models.Goal(
                user_id=user.id,
                **goal_data,
                is_active=True,
            )
            db.add(goal)
        
        db.commit()
        print(f"✅ Created {len(goals_data)} goals")
        
        # Generate comprehensive transactions (last 6 months)
        categories = [
            "Food & Dining", "Shopping", "Transportation", "Bills & Utilities",
            "Entertainment", "Healthcare", "Education", "Travel",
            "Home & Garden", "Personal Care", "Groceries", "Restaurants",
            "Gas", "Parking", "Public Transit", "Rideshare"
        ]
        
        merchants = {
            "Food & Dining": ["Starbucks", "McDonald's", "Subway", "Chipotle", "Pizza Hut"],
            "Shopping": ["Amazon", "Target", "Walmart", "Best Buy", "Costco"],
            "Transportation": ["Uber", "Lyft", "Shell", "Exxon", "Metro Transit"],
            "Bills & Utilities": ["Electric Company", "Water Department", "Internet Provider", "Phone Company"],
            "Entertainment": ["Netflix", "Spotify", "Movie Theater", "Concert Hall"],
            "Groceries": ["Whole Foods", "Trader Joe's", "Kroger", "Safeway"],
            "Restaurants": ["Olive Garden", "Red Lobster", "Local Restaurant", "Fast Food Chain"],
        }
        
        transactions = []
        checking_account = accounts[0]
        credit_account = accounts[2]
        
        # Generate transactions for last 6 months
        start_trans_date = now - timedelta(days=180)
        
        # Income transactions (bi-weekly)
        income_amount = 3500.00
        pay_date = start_trans_date
        while pay_date <= now:
            if pay_date.weekday() == 4:  # Friday
                transaction = models.Transaction(
                    user_id=user.id,
                    account_id=checking_account.id,
                    transaction_id=f"income_{pay_date.strftime('%Y%m%d')}",
                    amount=income_amount,
                    date=pay_date,
                    name="Salary Deposit",
                    category="Income",
                    merchant_name="Employer",
                    is_pending=False,
                )
                transactions.append(transaction)
                pay_date += timedelta(days=14)
            else:
                pay_date += timedelta(days=1)
        
        # Expense transactions (daily)
        for day_offset in range(180):
            trans_date = start_trans_date + timedelta(days=day_offset)
            
            # Skip weekends for some categories
            if trans_date.weekday() < 5:  # Weekday
                num_transactions = random.randint(2, 5)
            else:  # Weekend
                num_transactions = random.randint(1, 3)
            
            for _ in range(num_transactions):
                category = random.choice(categories)
                merchant_list = merchants.get(category, ["Generic Merchant"])
                merchant = random.choice(merchant_list)
                
                # Amount based on category
                if category in ["Food & Dining", "Groceries", "Restaurants"]:
                    amount = -random.uniform(5.00, 80.00)
                elif category == "Shopping":
                    amount = -random.uniform(20.00, 200.00)
                elif category in ["Transportation", "Gas", "Parking", "Public Transit", "Rideshare"]:
                    amount = -random.uniform(10.00, 50.00)
                elif category == "Bills & Utilities":
                    amount = -random.uniform(50.00, 150.00)
                elif category == "Entertainment":
                    amount = -random.uniform(10.00, 100.00)
                else:
                    amount = -random.uniform(5.00, 150.00)
                
                # Use credit card for 30% of transactions
                account = random.choice([credit_account, checking_account]) if random.random() < 0.3 else checking_account
                
                transaction = models.Transaction(
                    user_id=user.id,
                    account_id=account.id,
                    transaction_id=f"exp_{trans_date.strftime('%Y%m%d')}_{len(transactions)}",
                    amount=amount,
                    date=trans_date,
                    name=f"{merchant} Purchase",
                    category=category,
                    merchant_name=merchant,
                    is_pending=random.random() < 0.1,  # 10% pending
                )
                transactions.append(transaction)
        
        # Add all transactions
        for transaction in transactions:
            db.add(transaction)
        
        db.commit()
        print(f"✅ Created {len(transactions)} transactions")
        
        # Update account balances based on transactions
        for account in accounts:
            account_transactions = [t for t in transactions if t.account_id == account.id]
            total_amount = sum(t.amount for t in account_transactions)
            
            if account.type == "credit":
                account.balance = total_amount  # Credit cards show negative balance
            else:
                account.balance += total_amount
            
            db.add(account)
        
        db.commit()
        print(f"✅ Updated account balances")
        
        # Update budget current_spent based on actual transactions
        for budget in db.query(models.Budget).filter(models.Budget.user_id == user.id).all():
            budget_transactions = [
                t for t in transactions
                if t.category == budget.category
                and t.amount < 0
                and budget.start_date <= t.date <= budget.end_date
            ]
            actual_spent = abs(sum(t.amount for t in budget_transactions))
            
            # If actual spent is too low (less than 20% of budget), use a realistic percentage
            if actual_spent < budget.amount * 0.2:
                # Use the original spent percentage from budgets_data
                for bd in budgets_data:
                    if bd["category"] == budget.category:
                        budget.current_spent = budget.amount * bd["spent_pct"]
                        break
            else:
                budget.current_spent = actual_spent
            
            db.add(budget)
        
        db.commit()
        print(f"✅ Updated budget spending from transactions")
        
        print("\n" + "="*50)
        print("✅ COMPREHENSIVE DATA SEEDED SUCCESSFULLY!")
        print("="*50)
        print(f"\n📊 Summary:")
        print(f"   - Accounts: {len(accounts)}")
        print(f"   - Budgets: {len(budgets_data)}")
        print(f"   - Goals: {len(goals_data)}")
        print(f"   - Transactions: {len(transactions)}")
        print(f"\n🌐 Access:")
        print(f"   URL: http://localhost:3001")
        print(f"   Email: test@example.com")
        print(f"   Password: testpass123")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_comprehensive_data()

