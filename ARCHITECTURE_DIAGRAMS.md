# Multi-Step Registration System - Visual Architecture

## 📊 User Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER REGISTRATION JOURNEY                        │
└─────────────────────────────────────────────────────────────────────┘

START: User visits /accounts/register/
    ↓
┌──────────────────────────────────────────────────────────────┐
│  STAGE 1: PERSONAL INFORMATION (25% Progress)              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Progress: ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 25%         │
│  Steps: ● ─ ○ ─ ○ ─ ○                                      │
│         1   2   3   4                                        │
│                                                              │
│  Form Fields:                                               │
│  ├─ Username        [john_doe_________]  [✓ Available]     │
│  ├─ Email           [john@example.com_]  [✓ Valid]         │
│  ├─ First Name      [John_____________]                    │
│  └─ Last Name       [Doe______________]                    │
│                                                              │
│  Validation:                                                │
│  ✓ Username unique          [x] Duplicate username         │
│  ✓ Email valid format       [x] Invalid email format       │
│  ✓ Email unique             [x] Email already registered   │
│  ✓ All fields filled                                        │
│                                                              │
│  Actions: [← Back (disabled)]  [Next →]                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
    ↓ [Validated] Next button clicked
    ↓ Slide animation (500ms)
┌──────────────────────────────────────────────────────────────┐
│  STAGE 2: SUBSCRIPTION TIER SELECTION (50% Progress)       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Progress: ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 50%       │
│  Steps: ✓ ─ ● ─ ○ ─ ○                                      │
│         1   2   3   4                                        │
│                                                              │
│  Subscription Plans:                                        │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Individual ☑     │  │ Team             │               │
│  │ $9/month         │  │ $29/month        │               │
│  │ 5 uses/day       │  │ Unlimited uses   │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Business         │  │ Enterprise       │               │
│  │ $99/month        │  │ Custom Pricing   │               │
│  │ Full access      │  │ Dedicated        │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                              │
│  Use Cases (Select all that apply):                        │
│  ☑ Business intelligence & dashboards                      │
│  ☐ Personal data analysis                                  │
│  ☑ Team collaboration & reporting                         │
│  ☐ Client projects & delivery                              │
│  ☐ Data science & research                                │
│  ☐ Other                                                    │
│                                                              │
│  Validation:                                                │
│  ✓ Tier selected            [x] No tier selected          │
│  ✓ At least one use case (optional)                       │
│                                                              │
│  Actions: [← Back]  [Next →]                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
    ↓ [Validated] Next button clicked
    ↓ Slide animation (500ms)
┌──────────────────────────────────────────────────────────────┐
│  STAGE 3: PASSWORD SETUP (75% Progress)                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Progress: ████████████░░░░░░░░░░░░░░░░░░░░░░░░ 75%       │
│  Steps: ✓ ─ ✓ ─ ● ─ ○                                      │
│         1   2   3   4                                        │
│                                                              │
│  Password Requirements:                                     │
│  ✓ 8+ characters        ✓ Uppercase letter (A-Z)          │
│  ✓ Digit (0-9)          ✓ Special character (!@#$...)     │
│                                                              │
│  Password:      [SecurePass123!___________] [👁 Show]     │
│  Strength:      ██████████ STRONG (100%) [✓ Excellent]    │
│                 └─ Updates in real-time as you type ─┘    │
│                                                              │
│  Color Codes:                                               │
│  🔴 Weak (25%)   - Less than 2 requirements met           │
│  🟠 Fair (50%)   - 2 requirements met                     │
│  🟡 Good (75%)   - 3 requirements met                     │
│  🟢 Strong (100%) - All requirements met ✓               │
│                                                              │
│  Confirm:       [SecurePass123!___________] [👁 Show]     │
│  Match:         ✓ Passwords match         [✓ Green]       │
│                                                              │
│  Validation:                                                │
│  ✓ Password strong      [x] Password weak                  │
│  ✓ Passwords match      [x] Passwords don't match          │
│                                                              │
│  Actions: [← Back]  [Next →]                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
    ↓ [Validated] Next button clicked
    ↓ Slide animation (500ms)
┌──────────────────────────────────────────────────────────────┐
│  STAGE 4: TERMS & CONDITIONS (100% Progress)               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Progress: ████████████████░░░░░░░░░░░░░░░░░░░░ 100%      │
│  Steps: ✓ ─ ✓ ─ ✓ ─ ●                                      │
│         1   2   3   4                                        │
│                                                              │
│  Terms of Service:                                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ LuminaBI Terms of Service                           │ │
│  │                                                      │ │
│  │ 1. Service Terms                                    │ │
│  │ By using LuminaBI, you agree to comply with these  │ │
│  │ terms and conditions. Our service provides data    │ │
│  │ analytics and visualization tools...               │ │
│  │                                                      │ │
│  │ 2. Account Responsibility                          │ │
│  │ You are responsible for maintaining the            │ │
│  │ confidentiality of your account information...     │ │
│  │                                                      │ │
│  │ [... scroll for more ...]                          │ │
│  │                                                      │ │
│  │ 7. Changes to Terms                                │ │
│  │ We reserve the right to modify these terms at      │ │
│  │ any time. Continued use constitutes acceptance.    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                              │
│  Privacy Information:                                       │
│  ℹ️ Your data is protected with industry-standard         │
│     encryption. We do not share your data with third      │
│     parties without explicit consent.                      │
│     [Read Full Privacy Policy]                             │
│                                                              │
│  Acceptance:                                                │
│  ☑ I agree to the Terms of Service, Privacy Policy,      │
│    and Cookie Policy                                      │
│                                                              │
│  Confirmation:                                              │
│  ✓ By clicking Create Account, registration is            │
│    complete and verification email will be sent.          │
│                                                              │
│  Validation:                                                │
│  ✓ Terms checkbox checked  [x] Terms checkbox unchecked   │
│                                                              │
│  Actions: [← Back]  [Create Account ✓]                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
    ↓ [Validated] Create Account button clicked
    ↓ Form submission to backend
┌──────────────────────────────────────────────────────────────┐
│  BACKEND PROCESSING                                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Validate all fields (server-side)                      │
│     ├─ Username unique in database      [✓ PASS]         │
│     ├─ Email unique in database         [✓ PASS]         │
│     └─ Password strength verified       [✓ PASS]         │
│                                                              │
│  2. Create User object                  [✓ CREATED]       │
│     ├─ username: john_doe                                 │
│     ├─ email: john@example.com                            │
│     ├─ password: hashed (Argon2)                          │
│     └─ first/last names                                   │
│                                                              │
│  3. Create/Update UserProfile           [✓ UPDATED]       │
│     └─ preferred_subscription_tier: "team"               │
│                                                              │
│  4. Auto-create Trial Subscription      [✓ CREATED]       │
│     ├─ user: john_doe                                     │
│     ├─ plan: Team ($29/month)                            │
│     ├─ status: trial (30 days)                           │
│     └─ started_at: 2025-12-06                            │
│                                                              │
│  5. Create Email Verification Token     [✓ CREATED]       │
│     ├─ token: <secure_random_string>                      │
│     ├─ expires_at: 24 hours                               │
│     └─ verified: false                                    │
│                                                              │
│  6. Send Verification Email              [✓ SENT]         │
│     ├─ to: john@example.com                              │
│     ├─ subject: Verify your LuminaBI account             │
│     └─ link: https://luminabi.com/verify/<token>        │
│                                                              │
│  7. Log registration event               [✓ LOGGED]       │
│     ├─ timestamp: 2025-12-06T12:50:00Z                  │
│     ├─ user_id: 42                                        │
│     ├─ tier: team                                         │
│     └─ ip_address: 192.168.1.1                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
    ↓ Success response sent to frontend
    ↓ Redirect to login page
┌──────────────────────────────────────────────────────────────┐
│  SUCCESS! ✅                                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ✓ Account created successfully!                           │
│                                                              │
│  Message displayed to user:                                │
│  "Registration successful! Please check your email to      │
│   verify your account."                                    │
│                                                              │
│  Next Steps for User:                                       │
│  1. Check email (john@example.com)                         │
│  2. Click verification link                                │
│  3. Return to login page                                   │
│  4. Login with credentials                                 │
│  5. Access dashboard                                       │
│  6. Start using Team plan features                         │
│                                                              │
│  Database State:                                            │
│  ├─ User: john_doe (active)                               │
│  ├─ Profile: Team tier (stored)                           │
│  ├─ Subscription: Trial - Team plan (30 days)            │
│  ├─ Email Verification: Pending (token valid 24h)        │
│  └─ Login History: Registration logged                     │
│                                                              │
│  Redirect: /accounts/login/                                │
│  Display Message: "Check your email for verification      │
│                    link"                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
    ↓
END: User completes registration and checks email
```

---

## 🏗️ System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  register.html (1,382 lines)                                           │
│  ├─ Progress Bar Component                                             │
│  │  └─ progress-fill (0-100%)                                         │
│  ├─ Step Indicator Component                                          │
│  │  ├─ step-dot (1,2,3,4)                                             │
│  │  └─ step-connector (lines between dots)                           │
│  ├─ Form Stages (4 total)                                             │
│  │  ├─ Stage 1: Personal Information                                 │
│  │  │  └─ form-step#step1 (username, email, names)                  │
│  │  ├─ Stage 2: Subscription Tier                                   │
│  │  │  └─ form-step#step2 (tier options, use cases)                 │
│  │  ├─ Stage 3: Password Setup                                      │
│  │  │  └─ form-step#step3 (password, confirm, strength)             │
│  │  └─ Stage 4: Terms & Conditions                                  │
│  │     └─ form-step#step4 (terms, checkbox, submit)                 │
│  ├─ Navigation Buttons                                                │
│  │  ├─ btn-back (shows on stages 2+)                                │
│  │  ├─ btn-next (shows on stages 1-3)                               │
│  │  └─ btn-submit (shows on stage 4)                                │
│  └─ Styling & Animations                                             │
│     ├─ Glass-morphism panels                                        │
│     ├─ Gradient accents (cyan → purple)                             │
│     ├─ Ambient background blobs                                     │
│     └─ Smooth transitions (slideIn, slideOut)                       │
│                                                                          │
│  JavaScript Functions (register.html)                                  │
│  ├─ nextStep()           → Validate & move to next stage            │
│  ├─ previousStep()        → Return to previous stage                │
│  ├─ validateStep(step)    → Stage-specific validation               │
│  ├─ updateStep()          → Update UI for current step              │
│  ├─ checkPasswordStrength()→ Real-time strength meter              │
│  ├─ checkPasswordMatch()  → Real-time match validation             │
│  ├─ togglePassword()      → Show/hide password                      │
│  ├─ showError()           → Display error notification              │
│  └─ initializeFormHandlers()→ Setup event listeners                │
│                                                                          │
│  Form State (JavaScript object)                                        │
│  {                                                                      │
│    currentStep: 1-4,                                                  │
│    formData: {                                                        │
│      username, email, first_name, last_name,                       │
│      password, password_confirm,                                   │
│      subscription_tier, use_cases[], terms_accepted             │
│    }                                                                 │
│  }                                                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                ↓ HTTP POST
┌─────────────────────────────────────────────────────────────────────────┐
│                        MIDDLEWARE LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Django CSRF Protection                                                │
│  └─ Validates CSRF token in request                                  │
│                                                                          │
│  Request Processing                                                     │
│  ├─ Parse POST data                                                  │
│  ├─ Extract form fields                                              │
│  └─ Route to RegisterView                                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        BACKEND LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  accounts/views.py                                                      │
│  └─ RegisterView (FormView)                                            │
│     ├─ form_valid(form)                                               │
│     │  ├─ Extract form data                                          │
│     │  ├─ Create User object                                        │
│     │  ├─ Create/Get UserProfile                                    │
│     │  │  └─ Store preferred_subscription_tier                     │
│     │  ├─ Get SubscriptionPlan by tier                             │
│     │  ├─ Create Subscription (trial)                              │
│     │  ├─ Create EmailVerification token                           │
│     │  ├─ Send verification email                                  │
│     │  └─ Return success response                                  │
│     │                                                               │
│     ├─ form_invalid(form)                                            │
│     │  └─ Return form with errors                                  │
│     │                                                               │
│     └─ get_context_data(**kwargs)                                    │
│        └─ Pass form to template                                    │
│                                                                          │
│  accounts/forms.py (defined in views.py)                              │
│  └─ RegistrationForm (ModelForm)                                      │
│     ├─ Fields (from User model):                                     │
│     │  ├─ username                                                  │
│     │  ├─ email                                                     │
│     │  ├─ first_name                                                │
│     │  └─ last_name                                                 │
│     │                                                               │
│     ├─ Additional fields:                                            │
│     │  ├─ password                                                  │
│     │  ├─ password_confirm                                          │
│     │  ├─ subscription_tier (NEW)                                  │
│     │  └─ terms_accepted (NEW)                                     │
│     │                                                               │
│     └─ Validation methods:                                           │
│        ├─ clean_username()         → Check uniqueness              │
│        ├─ clean_email()            → Check uniqueness & format     │
│        ├─ clean()                  → Check passwords, strength     │
│        └─ clean_password()         → Strength validation           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATABASE LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Models:                                                                │
│                                                                          │
│  ┌─ User (Django built-in)                                            │
│  │  ├─ id (PK)                                                       │
│  │  ├─ username (unique)                                             │
│  │  ├─ email (unique)                                                │
│  │  ├─ password (hashed with Argon2)                                │
│  │  ├─ first_name                                                    │
│  │  ├─ last_name                                                     │
│  │  ├─ is_active                                                     │
│  │  └─ created_at (auto_now_add)                                     │
│  │                                                                     │
│  ├─ UserProfile (1-to-1 with User)                                   │
│  │  ├─ id (PK)                                                       │
│  │  ├─ user_id (FK → User)                                          │
│  │  ├─ bio                                                            │
│  │  ├─ avatar                                                         │
│  │  ├─ role                                                           │
│  │  ├─ theme                                                          │
│  │  ├─ language                                                       │
│  │  ├─ timezone                                                       │
│  │  ├─ email_notifications (boolean)                                │
│  │  ├─ preferred_subscription_tier (NEW)     ← CAPTURES TIER        │
│  │  ├─ is_email_verified (boolean)                                  │
│  │  ├─ created_at                                                    │
│  │  └─ updated_at                                                    │
│  │                                                                     │
│  ├─ EmailVerification (1-to-1 with User)                             │
│  │  ├─ id (PK)                                                       │
│  │  ├─ user_id (FK → User)                                          │
│  │  ├─ token (unique, secure)                                        │
│  │  ├─ expires_at (24 hours)                                        │
│  │  ├─ verified (boolean)                                            │
│  │  └─ verified_at (datetime)                                        │
│  │                                                                     │
│  └─ Subscription (Many-to-1 with User + Plan)                        │
│     ├─ id (PK)                                                       │
│     ├─ user_id (FK → User)                                          │
│     ├─ plan_id (FK → SubscriptionPlan)                              │
│     ├─ status: 'trial', 'active', 'paused', 'cancelled'            │
│     ├─ started_at                                                    │
│     ├─ ends_at                                                       │
│     └─ created_at                                                    │
│                                                                          │
│  Database Transactions:                                                │
│  ┌─ BEGIN TRANSACTION                                                 │
│  │  ├─ INSERT INTO User (username, email, password, ...)            │
│  │  ├─ INSERT INTO UserProfile (user_id, preferred_tier)           │
│  │  ├─ SELECT SubscriptionPlan WHERE name = 'Team'                 │
│  │  ├─ INSERT INTO Subscription (user_id, plan_id, status)         │
│  │  ├─ INSERT INTO EmailVerification (user_id, token, expires_at)  │
│  │  └─ COMMIT                                                        │
│  └─ Transaction atomicity ensures data integrity                     │
│                                                                          │
│  New Migration Applied:                                                │
│  └─ 0002_userprofile_preferred_subscription_tier                     │
│     └─ Adds CharField with 4 subscription tier choices              │
│        Default: 'individual' (for existing users)                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        EMAIL SERVICE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Email Verification Notification                                       │
│  ├─ To: john@example.com                                              │
│  ├─ Subject: Verify your LuminaBI Account                            │
│  ├─ Template: accounts/email/verify_email.txt                        │
│  └─ Body:                                                              │
│     │  Hi John,                                                       │
│     │                                                                 │
│     │  Welcome to LuminaBI! Please verify your email address        │
│     │  by clicking the link below:                                 │
│     │                                                                 │
│     │  https://luminabi.com/accounts/verify-email/TOKEN/           │
│     │                                                                 │
│     │  This link expires in 24 hours.                              │
│     │                                                                 │
│     │  Best regards,                                                 │
│     │  The LuminaBI Team                                            │
│     │                                                                 │
│  Welcome/Onboarding Email (optional future enhancement)               │
│  ├─ To: john@example.com                                              │
│  ├─ Subject: Welcome to Your Team Plan, John!                        │
│  └─ Body:                                                              │
│     │  Includes personalized onboarding based on tier                │
│     │  Links to feature documentation                                │
│     │  Invitation to team setup (if Team plan)                      │
│     │                                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        RESPONSE LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Response to Frontend (JSON):                                           │
│  {                                                                      │
│    "status": "success",                                                │
│    "message": "Registration successful! Check your email for link",   │
│    "redirect": "/accounts/login/",                                    │
│    "user_id": 42,                                                      │
│    "tier": "team",                                                     │
│    "trial_days": 30                                                    │
│  }                                                                      │
│                                                                          │
│  Frontend Actions:                                                      │
│  ├─ Display success message                                           │
│  ├─ Hide form                                                          │
│  ├─ Show "Check your email" prompt                                    │
│  ├─ Redirect to login after 3 seconds                                 │
│  └─ Clear form data                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
User Input → JavaScript Validation → Form State → Backend Validation → Database

┌──────────────────┐
│  User enters     │
│  username in     │
│  Stage 1 form    │
└────────┬─────────┘
         ↓
┌──────────────────────────────────────┐
│ JavaScript triggers:                 │
│ checkFieldValidity()                 │
│ (client-side only)                   │
└────────┬─────────────────────────────┘
         ↓
    [Valid?]
     ↙     ↘
   NO      YES
    ↓       ↓
 [RED] → [GREEN checkmark shows]
    ↓
  Shows error: "Username too short"
           ↓
     User corrects input
           ↓
         Repeats cycle
           ↓
  [User clicks Next Button]
         ↓
┌──────────────────────────────────────┐
│ Stage 1 Validation:                  │
│ • Username required (JS check)       │
│ • Email valid format (JS check)      │
│ • Email required (JS check)          │
│ • Names required (JS check)          │
└────────┬─────────────────────────────┘
         ↓
    [All valid?]
     ↙     ↘
   NO      YES
    ↓       ↓
 Error    [Proceed to Stage 2]
display         ↓
 msg    Form data stored in JS
    ↓         ↓
  Retry  [Animation slides in Stage 2]
         ↓
    [User selects tier and clicks Next]
         ↓
┌──────────────────────────────────────┐
│ Stage 2 Validation:                  │
│ • Tier selected (JS check)           │
│ • Use cases optional (JS check)      │
└────────┬─────────────────────────────┘
         ↓
    [Valid?]
     ↙     ↘
   NO      YES
    ↓       ↓
 Error   Proceed to
  msg    Stage 3
    ↓       ↓
  Retry  [Continue flow...]
         ↓
[User enters password and clicks Next]
         ↓
┌──────────────────────────────────────┐
│ Stage 3 Validation:                  │
│ • Length >= 8 (JS + real-time)       │
│ • Uppercase present (JS)             │
│ • Digit present (JS)                 │
│ • Special char (JS)                  │
│ • Passwords match (JS real-time)     │
└────────┬─────────────────────────────┘
         ↓
    [All valid?]
     ↙     ↘
   NO      YES
    ↓       ↓
Strength  Proceed to
 meter    Stage 4
 shows    (STRONG)
 color      ↓
 change   [Animation slides in Stage 4]
    ↓       ↓
  Shows "Next" disabled until fixed
              ↓
   [User accepts terms and clicks Create]
              ↓
   ┌────────────────────────────────────┐
   │ Final Form Submission              │
   │ POST /accounts/register/           │
   │ Body:                              │
   │ {                                  │
   │   username: "john_doe",            │
   │   email: "john@example.com",       │
   │   first_name: "John",              │
   │   last_name: "Doe",                │
   │   password: "SecurePass123!",      │
   │   password_confirm: "...",         │
   │   subscription_tier: "team",       │
   │   terms_accepted: true             │
   │ }                                  │
   │ Headers:                           │
   │ • X-CSRFToken: <csrf_token>       │
   │ • Content-Type: application/json   │
   └────────┬─────────────────────────────┘
            ↓
   ┌────────────────────────────────────┐
   │ Backend Server-Side Validation     │
   │ (accounts/views.py - RegisterView) │
   │                                    │
   │ 1. Check CSRF token               │
   │ 2. Form validation:               │
   │    • Username length/format       │
   │    • Email format                 │
   │    • Passwords match              │
   │    • Password strength            │
   │    • Tier value valid             │
   │ 3. Database checks:               │
   │    • Username unique              │
   │    • Email unique                 │
   └────────┬─────────────────────────────┘
            ↓
       [All valid?]
        ↙     ↘
      NO      YES
       ↓       ↓
   400 Error  ┌─────────────────────────┐
   returned   │ Create User Record      │
   to client  │ ├─ Save username        │
       ↓      │ ├─ Hash password        │
   Form re-   │ ├─ Save email           │
   displayed  │ ├─ Save names           │
   with       │ └─ Set is_active=true   │
   errors     └────────┬────────────────┘
                       ↓
              ┌─────────────────────────┐
              │ Create UserProfile      │
              │ ├─ user = new_user      │
              │ ├─ set tier             │
              │ └─ save()               │
              └────────┬────────────────┘
                       ↓
              ┌─────────────────────────┐
              │ Create Subscription     │
              │ ├─ Get Plan by tier     │
              │ ├─ Create Subscription  │
              │ │ ├─ user = new_user    │
              │ │ ├─ plan = selected    │
              │ │ ├─ status = "trial"   │
              │ │ └─ save()             │
              │ └─ Commit transaction   │
              └────────┬────────────────┘
                       ↓
              ┌─────────────────────────┐
              │ Create Email Token      │
              │ ├─ Generate token       │
              │ ├─ Set expiry (24h)     │
              │ └─ Save to DB           │
              └────────┬────────────────┘
                       ↓
              ┌─────────────────────────┐
              │ Send Verification Email │
              │ ├─ Get template         │
              │ ├─ Build URL with token │
              │ └─ Send via SMTP        │
              └────────┬────────────────┘
                       ↓
              ┌─────────────────────────┐
              │ Return 302 Redirect     │
              │ ├─ Location: /login/    │
              │ ├─ Message: Success     │
              │ └─ Status: Redirect     │
              └────────┬────────────────┘
                       ↓
       ┌───────────────────────────────┐
       │ Frontend handles redirect:    │
       │ ├─ Show success message       │
       │ ├─ Clear form                 │
       │ ├─ Redirect to login          │
       │ └─ Wait 3 seconds before nav  │
       └──────────────┬────────────────┘
                      ↓
       ┌───────────────────────────────┐
       │ User checks email:            │
       │ ├─ Receives verification link │
       │ ├─ Clicks link                │
       │ ├─ Email verified             │
       │ └─ Can now login              │
       └───────────────────────────────┘
```

---

## ✨ This comprehensive system ensures:

- **User Experience:** Smooth, guided registration with clear progress
- **Data Integrity:** Server-side validation prevents bad data
- **Security:** CSRF protection, password hashing, email verification
- **Scalability:** Database design supports growth
- **Maintainability:** Clear separation of concerns
- **Error Handling:** Graceful error messages and recovery

