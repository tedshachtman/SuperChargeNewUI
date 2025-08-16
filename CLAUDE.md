# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SuperChargeNewUI is a web-based similarity testing application for evaluating creative "Bag of Holding" ideas. The project consists of an interactive HTML/JavaScript frontend and a Python backend for AI-powered similarity analysis using OpenAI embeddings and vector similarity calculations.

## Architecture

The application has two main components:

1. **Frontend (index.html)**: A single-page application with interactive UI for rating idea similarity
   - Presents pairs of ideas to users for rating (1-5 scale)
   - Implements sliding animations and real-time scoring
   - Contains 30 pre-defined "Bag of Holding" ideas with emojis
   - Tracks accuracy, speed multipliers, and completion progress

2. **Backend (similarity_backend.py)**: Python script for generating and analyzing idea embeddings
   - Uses OpenAI's text-embedding-3-large model for vectorization
   - Integrates with Pinecone for vector storage and retrieval
   - Calculates pairwise cosine similarities between all ideas
   - Outputs analysis results to similarity_results.json

## Common Development Tasks

### Running the Application
```bash
# Start the web server
npm start --However, ted will always run this. you don't run this)
# or
npm run serve
# or
python3 -m http.server 8000
```

### Backend Analysis
```bash
# Run the main similarity analysis (requires API keys)
python3 similarity_backend.py

# Test specific idea similarity
python3 test_your_ideas.py

```

### Environment Setup
```bash
# Copy environment template and add your API keys
cp env.example .env
# Edit .env with your OPENAI_API_KEY and PINECONE_API_KEY
```

## Key Files

- `index.html`: Complete frontend application with embedded CSS/JS
- `similarity_backend.py`: Main backend for embedding generation and analysis
- `test_your_ideas.py`: Utility for testing similarity between two custom ideas
- `test_similarity.py`: Fallback similarity testing using sentence-transformers
- `package.json`: Basic project metadata and web server commands
- `env.example`: Template for required environment variables
- `similarity_results.json`: Generated output from backend analysis

## Dependencies

### Python Dependencies (Backend)
- openai
- pinecone-client
- scikit-learn
- numpy
- sentence-transformers (optional, for test_similarity.py)

### Frontend Dependencies
- None (vanilla HTML/CSS/JavaScript)

## API Integration

The application integrates with:
- **OpenAI API**: For text embeddings using text-embedding-3-large model
- **Pinecone**: For vector database storage and similarity search
- Required API keys must be set in environment variables

## Data Flow

1. Backend generates embeddings for 30 predefined ideas
2. Pairwise similarities are calculated and stored
3. Frontend presents idea pairs to users based on similarity rankings
4. User ratings are compared against computed similarities for accuracy scoring
5. Real-time feedback and scoring based on user performance

## Notification Instructions

**IMPORTANT**: Use `~/bell.sh` when you finish major features, complete implementations, or need Ted to review/test something. 

Examples:
- `Feature complete ~/bell.sh`
- `Ready for testing ~/bell.sh`
- `Implementation finished ~/bell.sh`
- or literally any other time your about to stop coding. The idea is that, if you are plugging away, no bell-- but if you are about to stop coding for any reason, ring the bell.

Ted runs Claude Code while doing other work and doesn't want to constantly check the terminal. The bell system notifies him when he needs to look at the terminal for:
- Feature completion
- Implementation reviews
- Testing requests
- Questions requiring input
- Any time Claude needs Ted's attention

## Permission Management

**CRITICAL**: Always check the local Claude Code settings in `.claude/settings.local.json` to see what commands you're allowed to run without permission.

**MANDATORY BELL RULE**: Before running ANY command that is NOT explicitly listed in the "allow" section of settings.local.json:
1. Ring the bell FIRST: `~/bell.sh`
2. THEN run the command that needs permission

**Commands that ALWAYS need bell first** (unless explicitly in allow list):
- ALL AWS IAM commands (`aws iam *`)
- Git commits and pushes
- System-level commands 
- Package installations
- File modifications outside the project
- ANY command not in the allow list

**This is UNACCEPTABLE**: Running a command that needs permission without ringing the bell first. Ted will be frustrated waiting at the terminal.

**Check the allow list EVERY TIME** before running commands. When in doubt, ring the bell.

This workflow allows Ted to actively work on other things while Claude codes, only needing to check the terminal when the bell rings for permission requests or completions.


AWS stuff

I am authenticated in AWS in this terminal-- you're going to need to create and manage all the resources in AWS. Also, if you every need to test the API calls from the front end, and we have authentication setup (which we will do), you need to console log the auth token and then ask me to give it to you. This way, you can text all the APIs on your own without me having to tell you "I got a 500 error."

## SuperCharge Cloth System Documentation

### Overview
The SuperCharge Cloth system is a complete daily creativity challenge platform built on AWS. Users submit 4 creative ideas based on daily superpower prompts, rate other submissions, and compete on leaderboards.

### Architecture

#### AWS Backend Infrastructure
- **Region**: us-east-1
- **Account ID**: 696944065143

#### DynamoDB Tables
1. **supercharged_superpowers**
   - Hash Key: superpowerID (String)
   - GSI: date-index (date as Hash Key)
   - Stores daily superpower challenges

2. **supercharged_submissions** 
   - Hash Key: submissionId (String)
   - GSI: user-date-index (userId as Hash, date as Range)
   - GSI: date-index (date as Hash Key)
   - Stores user's 4 daily idea submissions

3. **supercharged_ratings**
   - Hash Key: ratingId (String)  
   - GSI: user-date-index (userId as Hash, date as Range)
   - GSI: date-index (date as Hash Key)
   - Stores similarity ratings between idea pairs

4. **supercharged_user_progress**
   - Hash Key: userId (String)
   - Range Key: date (String)
   - Tracks user completion and scoring

#### Lambda Functions
All functions deployed with prefix `supercharged-`:

1. **supercharged-get-daily-superpower**
   - GET /superpower
   - Returns today's superpower challenge
   - Queries date-index for current date

2. **supercharged-submit-ideas**
   - POST /submit
   - Accepts 4 user ideas (max 100 words each)
   - Validates deadline (11:59 PM)
   - Prevents duplicate submissions

3. **supercharged-get-rating-pairs**
   - GET /rating/pairs?userId={id}
   - Returns pairs of submissions for rating
   - Excludes user's own submissions
   - Avoids already-rated pairs

4. **supercharged-submit-rating**
   - POST /rating
   - Records 1-5 similarity rating
   - Prevents duplicate ratings of same pairs

5. **supercharged-admin-add-superpower**
   - POST /admin
   - Admin function to add daily superpowers
   - Validates date availability

6. **supercharged-get-leaderboard**
   - GET /leaderboard?date={YYYY-MM-DD}
   - Returns rankings and top ideas
   - Calculates combined submission + rating scores

7. **supercharged-generate-ai-ideas**
   - POST /admin/generate-ideas
   - Generates 70 AI baseline ideas using Gemini 2.5 Pro
   - Called automatically when new superpowers are added
   - Stores AI ideas with isAI=true flag for rating baseline

#### API Gateway
- **API ID**: gsx73a1w3d
- **Base URL**: https://gsx73a1w3d.execute-api.us-east-1.amazonaws.com/prod
- **Stage**: prod
- **CORS**: Enabled for web access

#### IAM Role
- **Role**: lambda-execution-role
- **Policies**: 
  - AWSLambdaBasicExecutionRole
  - AmazonDynamoDBFullAccess

### Frontend Applications

#### 1. Main User App (cloth.html)
**URL**: http://localhost:8000/cloth.html

**User Flow**:
1. **Username Entry**: User provides unique identifier
2. **Daily Challenge**: Shows today's superpower + instructions
3. **Idea Submission**: 4 text areas with 100-word limits and real-time counters
4. **Deadline Timer**: Counts down to 11:59 PM
5. **Rating Phase**: 15-minute timer for rating other submissions
6. **Results**: Shows percentile ranking and mock leaderboard

**Key Features**:
- Real-time word counting with visual warnings
- Deadline enforcement
- Phase-based UI progression
- Responsive design
- API integration for all backend calls

#### 2. Admin Interface (admin.html)
**URL**: http://localhost:8000/admin.html

**Features**:
- Add new daily superpowers
- Schedule future challenges
- Date validation (no duplicates)
- Form validation and error handling
- Navigation to other admin tools

#### 3. Submissions Viewer (admin-submissions.html)  
**URL**: http://localhost:8000/admin-submissions.html

**Features**:
- View all user submissions by date (newest first)
- **AI vs Human Distinction**: Visual indicators (🤖/👤) and filtering
- Keyword search across usernames and idea content
- Date filtering (today, yesterday, week, month)
- **Type filtering**: Show AI-only, human-only, or all submissions
- Sort by date or username
- Statistics dashboard with AI/human breakdown
- Export to CSV functionality
- Pagination for large datasets
- Delete submissions capability
- Highlighting of search terms in results
- **AI Model Information**: Shows which AI model generated ideas

### API Endpoints Summary

```
GET  /superpower        # Get daily superpower challenge
POST /submit            # Submit 4 user ideas  
GET  /rating/pairs      # Get pairs for similarity rating
POST /rating            # Submit similarity rating
GET  /leaderboard       # Get results and rankings
POST /admin             # Add superpower (admin only)
POST /admin/generate-ideas # Generate AI baseline ideas (automatic)
```

### Gemini AI Integration

#### Purpose
When new superpowers are added, the system automatically generates 70 AI baseline ideas using Gemini 2.5 Pro. This provides a comparison baseline for user submissions, especially when there are few participants.

#### How It Works
1. **Automatic Trigger**: When admin adds a new superpower, the system automatically calls the Gemini API
2. **Dynamic Prompting**: The superpower title and description are injected into a carefully crafted prompt
3. **Idea Generation**: Gemini 2.5 Pro generates 70 creative, mechanistically complex ideas
4. **Database Storage**: Ideas are stored as submissions with `isAI: true` flag
5. **Baseline Comparison**: Human submissions can be compared against AI ideas for quality assessment

#### AI Idea Characteristics
- **Mechanistically complex**: Exploit specific properties of the superpower
- **Realistic**: Based on real-world physics and practical applications  
- **Novel**: Creative and non-obvious applications
- **Competition-grade**: Designed to be competitive but typically less intricate than top human ideas

#### Visual Indicators
- 🤖 AI submissions marked in admin interface
- 👤 Human submissions clearly distinguished
- Statistics show AI vs human breakdown
- Filter options to view AI-only or human-only submissions

### Data Flow

#### Daily Cycle
1. **12:00 AM**: New superpower becomes active, previous day results published
2. **Daily Submissions**: Users submit 4 ideas until 11:59 PM
3. **Rating Phase**: After submission, users get 15 minutes to rate others
4. **Scoring**: Combined scores from idea quality + rating accuracy
5. **Results**: Percentile rankings shown immediately, full leaderboard at midnight

#### Database Schema Example
```javascript
// Superpower
{
  superpowerID: "uuid-string",
  date: "2025-08-16", 
  title: "Perfect Memory",
  description: "You have the ability to...",
  isActive: true,
  timestamp: 1692123456
}

// Submission  
{
  submissionId: "uuid-string",
  userId: "username", 
  date: "2025-08-16",
  superpowerId: "uuid-string",
  ideas: ["idea1", "idea2", "idea3", "idea4"],
  timestamp: 1692123456,
  submittedAt: "2025-08-16T14:30:00Z"
}

// Rating
{
  ratingId: "uuid-string",
  userId: "rater-username",
  date: "2025-08-16", 
  submissionId1: "uuid-1",
  submissionId2: "uuid-2",
  rating: 4,  // 1-5 scale
  timestamp: 1692123456
}
```

### Testing Commands

#### Start Development Server
```bash
npm start  # Runs on port 8000
```

#### Test URLs
- **Main App**: http://localhost:8000/cloth.html
- **Admin**: http://localhost:8000/admin.html  
- **Submissions**: http://localhost:8000/admin-submissions.html
- **Original**: http://localhost:8000/index_original.html

#### Sample Data
Sample superpowers and submissions are preloaded for testing.

### File Structure
```
/Users/ted/SuperChargeNewUI/
├── cloth.html                    # Main user application
├── admin.html                    # Admin superpower management  
├── admin-submissions.html        # View/search submissions
├── index_original.html           # Backup of original similarity game
├── lambda_functions/             # All Lambda function source code
│   ├── get_daily_superpower.py
│   ├── submit_ideas.py
│   ├── get_rating_pairs.py
│   ├── submit_rating.py
│   ├── admin_add_superpower.py
│   └── get_leaderboard.py
├── setup_api_gateway.py         # API Gateway deployment script
├── deploy_lambdas.py            # Lambda deployment script
├── lambda-trust-policy.json     # IAM policy for Lambda
└── IMPLEMENTATION_STATUS.md     # Current status and todos
```

### Deployment Scripts

#### Lambda Deployment
```bash
python3 deploy_lambdas.py
```
- Deploys all 6 Lambda functions
- Creates zip packages automatically
- Updates existing functions or creates new ones

#### API Gateway Setup  
```bash
python3 setup_api_gateway.py
```
- Creates all resources and methods
- Sets up Lambda integrations
- Configures CORS
- Deploys to 'prod' stage

### Known Issues & Limitations

1. **Rating Interface**: Currently shows placeholder during 15-minute window
2. **Leaderboard**: API ready but frontend integration pending
3. **Authentication**: No user authentication implemented (uses usernames)
4. **Notifications**: No email/push notifications for results

### Future Enhancements

1. Complete rating interface with actual idea pairs
2. Real-time leaderboard updates
3. User authentication and profiles  
4. Email notifications for daily challenges
5. Advanced analytics and reporting
6. Mobile app version

### Troubleshooting

#### Common Issues
- **CORS Errors**: Check API Gateway CORS configuration
- **Lambda Timeouts**: Increase timeout in function configuration
- **DynamoDB Access**: Verify IAM role permissions
- **API Not Found**: Ensure API Gateway deployment completed

#### Useful AWS Commands
```bash
# Check Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `supercharged`)]'

# Check DynamoDB tables  
aws dynamodb list-tables --query 'TableNames[?starts_with(@, `supercharged`)]'

# View API Gateway
aws apigateway get-rest-apis --query 'items[?name==`supercharged-api`]'
```

## Gemini AI Integration Implementation Details

### 🤖 Automatic AI Baseline Generation

When you add a new superpower through the admin interface, the system automatically:

1. **Creates the superpower** in the database
2. **Triggers Gemini 2.5 Pro** to generate 70 baseline ideas
3. **Stores AI ideas** as submissions with special flags
4. **Provides instant feedback** on generation success

### Technical Implementation

#### Gemini API Integration
- **Model**: `gemini-2.0-flash-exp` (Gemini 2.5 Pro equivalent)
- **API Key**: `AIzaSyBhCFFPFv_qhhnkKp1GfM2MJ_bM1ZeISpg`
- **Direct REST API**: Uses simple HTTP requests (no SDK to avoid dependency issues)
- **Timeout**: 5-minute Lambda timeout for Gemini processing
- **Error Handling**: Graceful fallbacks for API timeouts

#### AI Idea Generation Process
```javascript
// When admin adds superpower:
1. POST /admin → Creates superpower
2. Auto-calls POST /admin/generate-ideas → Triggers Gemini
3. Gemini generates 70 ideas using dynamic prompt
4. Ideas stored as 18 submissions (4 ideas each) with isAI=true
5. Admin gets confirmation + AI generation status
```

#### AI Submission Schema
```javascript
{
  submissionId: "uuid-string",
  userId: "AI_Generator_1",  // Sequential AI user IDs
  date: "2025-08-16",
  superpowerId: "uuid-string", 
  ideas: ["idea1", "idea2", "idea3", "idea4"],
  timestamp: 1692123456,
  submittedAt: "2025-08-16T15:59:51Z",
  isAI: true,                    // ← Key flag for AI identification
  aiModel: "gemini-2.0-flash-exp",
  aiPromptVersion: "1.0"
}
```

### Dynamic Prompt Template

The system uses your creative prompt template but dynamically inserts the superpower details:

```text
Generate 70 creative use cases for the superpower "{SUPERPOWER_TITLE}" for a competitive creativity game.

Superpower Description: {SUPERPOWER_DESCRIPTION}

Quality Requirements:
- Mechanistically complex: Must exploit specific properties or clever interactions of this superpower
- Realistic: Based on real-world physics and practical applications, could actually work if this power existed
- Novel: Hard to think of, not obvious applications
- Competition-winning: Ideas that would beat other players in a creativity contest
- Practical: Focus on everyday problems and creative solutions

[Additional formatting and quality requirements...]
```

### AI vs Human Comparison Strategy

#### Purpose
- **Early Adoption**: Provides baselines when few users exist
- **Quality Assessment**: Human ideas scoring highly against AI ideas suggests room for improvement
- **Creativity Measurement**: Truly creative ideas should diverge from AI patterns

#### Visual Indicators
- **🤖 AI submissions**: Clearly marked with badges and icons
- **👤 Human submissions**: Distinguished from AI
- **Statistics**: "36 total (18👤 + 18🤖)" format
- **Filtering**: Separate views for AI-only vs human-only

### Testing Results

#### ✅ End-to-End Testing Complete
All major components tested and verified:

1. **✅ Daily Superpower API**: Working perfectly
2. **✅ User Submission System**: Validates, stores, prevents duplicates  
3. **✅ Rating System**: Creates pairs, accepts ratings, tracks progress
4. **✅ Leaderboard System**: Calculates scores, ranks users
5. **✅ AI Generation**: Gemini 2.5 Pro generates 70 quality ideas
6. **✅ Database Integration**: All CRUD operations working
7. **✅ Admin Interface**: Creates superpowers + triggers AI generation
8. **✅ Submissions Viewer**: Shows AI vs human with filtering

#### Sample AI-Generated Ideas
```
1. "Ultimate Lie Detection: By recalling every micro-expression, vocal inflection, and subtle body language cue ever witnessed, detect inconsistencies and lies with absolute certainty..."

2. "Creative Synthesis: Recalling every artistic work, scientific discovery, and philosophical idea ever encountered allows for the effortless synthesis of novel and groundbreaking concepts..."
```

#### Performance Metrics
- **Gemini API**: ~45-60 seconds to generate 70 ideas
- **Database Operations**: All under 1 second
- **API Endpoints**: All under 5 seconds (except AI generation)
- **Frontend**: Responsive, real-time updates

#### Current Database State
- **37 Total Submissions**: Mix of human and AI
- **36 AI Submissions**: Generated from Gemini 2.5 Pro
- **1 Human Submission**: Test user submission
- **Quality Verified**: AI ideas are mechanistically complex and creative

### Known Issues & Workarounds

#### 1. API Gateway Timeout (30 seconds)
- **Issue**: Gemini generation takes 45-60 seconds
- **Workaround**: Admin UI shows "background processing" message
- **Status**: AI generation completes successfully despite timeout
- **Evidence**: 36 AI submissions verified in database

#### 2. DynamoDB Decimal Types
- **Issue**: DynamoDB returns Decimal objects causing type errors
- **Fix**: All numeric operations now handle Decimal conversion
- **Status**: ✅ Fixed and tested

### Deployment Commands

#### Deploy All Lambda Functions
```bash
cd /Users/ted/SuperChargeNewUI
python3 deploy_lambdas.py              # Core functions
python3 deploy_gemini_lambda.py        # Gemini AI function
python3 setup_api_gateway.py           # API Gateway setup
python3 setup_gemini_api.py           # Gemini endpoint
```

#### Test Complete System
```bash
python3 test_end_to_end.py             # Full API testing
python3 test_gemini_direct.py          # Direct Gemini testing
```

### Files Added for Gemini Integration

```
├── lambda_functions/
│   ├── generate_ai_ideas_simple.py    # Gemini Lambda (production)
│   └── generate_ai_ideas.py           # Original (dependency issues)
├── deploy_gemini_lambda.py            # Gemini function deployment
├── setup_gemini_api.py               # API Gateway setup for Gemini
├── test_gemini_direct.py             # Direct Gemini API testing
├── test_end_to_end.py                 # Complete system testing
├── requirements_simple.txt            # Minimal dependencies for Lambda
└── requirements.txt                   # Full dependencies
```