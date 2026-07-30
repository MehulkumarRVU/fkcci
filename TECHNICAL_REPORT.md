# PocketCoach AI: Technical Project Report

## 1. Introduction

PocketCoach AI is a full-stack web application designed to provide real-time sports technique coaching using computer vision and pose analysis. The system uses a webcam, MediaPipe Pose detection, and a backend AI analysis engine to evaluate an athlete’s movement and provide instant feedback. The project focuses on indoor sports such as Table Tennis, Boxing, and Badminton, while also supporting a broader catalog of sports through a modular analysis framework.

The project was developed as an end-to-end solution that combines:
- A browser-based frontend for user interaction and video capture
- A FastAPI backend for authentication, session management, and AI analysis
- A relational database for storing athlete profiles, sessions, and skills
- A modular pose analysis system that can be extended to additional sports

---

## 2. Project Objective

The main objective of the project is to create an accessible and intelligent coaching tool that helps athletes improve their movement patterns, posture, balance, and technique through real-time visual analysis. The system aims to provide:
- Real-time pose tracking from a webcam
- Immediate visual and text-based feedback
- Sport-specific technique guidance
- Session history and progress tracking
- Secure user authentication and role-based access

The system is intended for beginners and intermediate athletes who want personalized feedback without requiring a human coach at all times.

---

## 3. Problem Statement

Traditional sports coaching often requires live supervision by a coach or trainer. This can be expensive, inaccessible, or inconvenient, especially for individuals practicing at home or in self-paced environments. In addition, many athletes struggle to self-evaluate their motion and identify subtle technique mistakes.

PocketCoach AI addresses this problem by offering an automated coaching experience that uses computer vision to analyze posture and movement in real time. The system can help users understand whether they are holding the correct form, maintaining balance, and executing fundamental movement patterns effectively.

---

## 4. Scope of the Project

The project consists of five major functional areas:

1. User management and authentication
2. Training session management
3. Skill library and coaching guidance
4. Pose detection and real-time feedback
5. Analytics and performance summaries

The implementation covers both the software architecture and the interactive application workflow required for actual use.

---

## 5. Functional Requirements

### 5.1 User Registration and Authentication
The application should allow users to:
- Create an athlete account
- Log in securely with username and password
- Receive an authentication token
- Maintain a session after login
- Access protected routes only after authentication

### 5.2 Session Management
The application should support:
- Creating new training sessions
- Viewing past sessions
- Updating session performance data
- Deleting sessions if needed
- Summarizing training statistics

### 5.3 Skill Library
The application should provide:
- A database of sports-specific skills
- Guidance and technique tips for each skill
- Common mistakes and safety warnings
- The ability to seed default data for initial use

### 5.4 Real-Time Pose Analysis
The application should:
- Access the user's camera
- Detect body pose landmarks in real time
- Send pose data to the backend for analysis
- Return technique feedback and scoring

### 5.5 Analytics Dashboard
The system should present:
- Performance score summaries
- Average technique accuracy
- Balance scores
- Recent training history

---

## 6. Non-Functional Requirements

The system was designed with the following non-functional considerations:
- Usability: simple browser-based interface
- Extensibility: modular sports analyzers
- Maintainability: separation of frontend, backend, and data layers
- Security: JWT-based authentication and password hashing
- Performance: lightweight feedback processing for live sessions

---

## 7. System Architecture

The project follows a three-tier architecture:

### 7.1 Presentation Layer (Frontend)
The frontend is built using:
- HTML5 for page structure
- CSS3 for responsive styling
- Vanilla JavaScript for client-side logic

The frontend provides:
- Landing page
- Login and signup screens
- Dashboard
- Session management page
- Training interface with live camera feed
- Profile management page

### 7.2 Application Layer (Backend)
The backend is built with FastAPI, a modern Python web framework that supports async APIs and automatic OpenAPI documentation. It handles:
- Authentication
- Session creation and updates
- Skill retrieval and seeding
- Pose analysis requests
- Analytics and summary generation

### 7.3 Data Layer (Database)
The application uses SQLite with SQLAlchemy ORM. SQLite is suitable for local development and lightweight deployment. The database stores:
- Athlete profiles
- Training sessions
- Skills
- Refresh tokens

---

## 8. Technology Stack

### 8.1 Backend Technologies
- Python 3.8+
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic
- Python-Jose (JWT support)
- Passlib / bcrypt-compatible hashing
- MediaPipe-compatible pose analysis integration

### 8.2 Frontend Technologies
- HTML
- CSS
- JavaScript
- MediaPipe Pose (loaded from CDN)
- Browser camera access via Web APIs

### 8.3 Development and Testing Tools
- Pytest
- FastAPI test client patterns
- Browser-based manual validation
- SQLAlchemy database initialization scripts

---

## 9. Project Structure

The repository is organized into the following main directories:

### Backend
- backend/main.py: FastAPI application entry point
- backend/app/config.py: application configuration and environment settings
- backend/app/database.py: database initialization and session factory
- backend/app/models/: ORM models for athletes, sessions, skills, and refresh tokens
- backend/app/routes/: API endpoints for authentication, sessions, skills, analysis, and analytics
- backend/app/pose_engine/: pose analysis engine and sport-specific analyzers
- backend/app/sports_registry.py: central registry of supported sports

### Frontend
- frontend/index.html: landing page
- frontend/pages/: login, dashboard, profile, session pages
- frontend/js/: app logic, authentication, session handling, pose detection, and sports analysis modules
- frontend/css/styles.css: styling for the interface

---

## 10. Backend Design and Implementation

### 10.1 Application Initialization
The backend entry point is defined in backend/main.py. During startup, the application:
- Initializes the database
- Validates security settings
- Configures CORS middleware
- Registers API routers
- Exposes health and root endpoints

### 10.2 Configuration Management
Configuration is handled through the settings module in backend/app/config.py. The app uses environment variables for:
- Secret key for JWT signing
- JWT algorithm
- Token expiration duration
- Database URL
- Rate limiting configuration
- Environment mode

### 10.3 Database Design
The database uses SQLAlchemy declarative models.

#### Athlete Model
The Athlete model stores:
- personal identity fields such as email and username
- hashed password
- role and coach relationship information
- sport type and linked sports
- skill level and physical profile details
- training statistics and performance metrics

#### Session Model
The Session model stores:
- athlete reference
- sport type
- session type
- timestamps and duration
- performance metrics
- detailed session data in JSON format

#### Skill Model
The Skill model stores:
- skill name
- associated sport
- description and instructional content
- common mistakes and safety warnings
- difficulty level and focus area

### 10.4 Authentication Flow
The authentication subsystem uses JWT tokens. The flow is:
1. User provides credentials
2. Server verifies username and password
3. Server issues an access token and a refresh token
4. Protected endpoints require the access token
5. Refresh tokens can be used to obtain a new access token

Password hashing uses a secure hashing approach and is verified before authentication succeeds.

### 10.5 Session Handling
The session API allows the frontend to:
- Start a new training session
- Update it with performance measures
- Summarize aggregate training results
- Retrieve all sessions for a specific athlete

The backend also updates athlete-level performance statistics when a session is marked completed.

---

## 11. Frontend Design and Implementation

### 11.1 User Interface
The frontend is intentionally lightweight and does not rely on heavy frameworks. It uses standard browser technologies so the application is easy to run and inspect.

The interface includes:
- Landing page with sports selection
- Login and signup forms
- Dashboard with overview cards and statistics
- Live session page containing video and feedback panels
- Profile page for personal details and preferences

### 11.2 Pose Detection Module
The pose detection module is implemented in frontend/js/pose-detection.js. It uses MediaPipe Pose to:
- Access the camera stream
- Detect pose landmarks frame by frame
- Draw pose connections on a canvas
- Send landmark data to the analysis logic

### 11.3 Sports Analysis Module
The sports analysis module in frontend/js/sports-analyzer.js provides:
- Angle calculations between body joints
- Distance calculations between points
- Local feedback heuristics for stance, balance, and posture
- Basic sport-specific guidance for Boxing, Table Tennis, Badminton, and others

This module provides immediate on-screen visual feedback while the backend performs more detailed analysis.

---

## 12. Pose Analysis Engine

The backend pose analysis system is modular and extensible.

### 12.1 Analyzer Factory Pattern
The analyzer factory in backend/app/pose_engine/analyzer_factory.py dynamically creates the correct analyzer based on the selected sport type. This approach allows the system to support multiple sports without hard-coding all logic into a single module.

### 12.2 Base Analyzer Interface
All analyzers inherit from a base interface that requires methods for:
- analyzing a single frame
- analyzing an entire session
- returning supported skills

### 12.3 Supported Sports
The system currently supports a large set of sports, including:
- Table Tennis
- Boxing
- Badminton
- Tennis
- Pickleball
- Squash
- Kickboxing
- Muay Thai
- Karate
- Taekwondo
- Judo
- Brazilian Jiu-Jitsu
- Wrestling
- Fencing
- Basketball
- Volleyball
- Handball
- Indoor Archery
- AI Gym Coach
- Stretching
- Mobility Training
- Rehabilitation
- Home Workouts
- Calisthenics

This broad support demonstrates the extensibility of the architecture.

---

## 13. API Design

The project exposes a RESTful API under the /api path.

### 13.1 Authentication Endpoints
- POST /api/auth/signup: Create a new athlete account
- POST /api/auth/signup-coach: Create a coach account
- POST /api/auth/login: Authenticate user and return tokens
- GET /api/auth/me: Retrieve logged-in athlete information
- PUT /api/auth/profile: Update profile information
- POST /api/auth/refresh: Refresh access token

### 13.2 Session Endpoints
- POST /api/sessions/: Create a session
- GET /api/sessions/: List sessions for the authenticated athlete
- GET /api/sessions/{id}: Retrieve a session by ID
- PUT /api/sessions/{id}: Update session metrics
- DELETE /api/sessions/{id}: Delete a session
- GET /api/sessions/stats/summary: Retrieve summary statistics

### 13.3 Skill Endpoints
- GET /api/skills/: Retrieve skills
- GET /api/skills/{id}: Retrieve a specific skill
- POST /api/skills/: Create a new skill
- POST /api/skills/seed: Seed the database with default sports skills

### 13.4 Analysis Endpoints
- POST /api/analysis/analyze: Analyze a sequence of pose frames
- POST /api/analysis/realtime-feedback: Return feedback for a single frame

The API is documented automatically by FastAPI through the /docs endpoint.

---

## 14. Data Flow

A typical workflow in the system is as follows:

1. The athlete opens the frontend application.
2. The user signs up or logs in.
3. The frontend requests authentication and receives a token.
4. The athlete starts a session and selects a sport and skill.
5. The browser accesses the camera and captures pose frames.
6. Pose landmarks are sent to the analysis route.
7. The backend uses the appropriate analyzer to evaluate the movement.
8. Feedback and scoring are returned to the frontend.
9. The athlete receives live coaching guidance and can review the session later.

This creates a real-time feedback loop between the camera, the analysis engine, and the user interface.

---

## 15. Security Considerations

The project includes several security-related features:
- Password hashing for user credentials
- JWT-based authentication for protected resources
- Refresh token support for session continuity
- Read/write access restrictions tied to authenticated users
- Role-based route protection for coach-related actions

However, the project also contains certain areas that would need hardening for production use, such as:
- CORS being set to allow all origins
- The default secret key being used unless configured properly
- SQLite being suitable for development but not ideal for high-concurrency production systems

---

## 16. Testing and Validation

The repository includes several test files that cover:
- authentication flows
- session management
- role-based access control
- rate limiting
- analytics behavior
- pose engine expectations

Testing is an important component because it validates not only functionality but also the reliability of the authentication and analysis pipeline.

The testing structure includes:
- backend/tests/
- root-level test files such as test_login.py and test_coach_dashboard.py

---

## 17. Strengths of the Project

The project demonstrates several strong design features:
- A clear separation between frontend and backend layers
- A modular AI analysis architecture
- Support for multiple sports through a registry-driven system
- A practical and usable interface for real-time coaching
- A database-backed session and profile system
- Good extensibility for future improvements

---

## 18. Limitations and Challenges

Although the project is comprehensive, it also has some limitations:
- The pose analysis is not a full professional biomechanics engine
- Some feedback logic is heuristic rather than highly accurate biomechanical modeling
- The system currently relies on local development-friendly infrastructure
- The frontend is plain JavaScript, which is simple but less scalable than modern frameworks
- The current deployment approach is not yet production-optimized

These limitations are acceptable for an academic or prototype-level implementation, but they would need refinement for commercial deployment.

---

## 19. Future Enhancements

Several improvements could be made in future versions:
- Add more accurate and sport-specific biomechanical analysis models
- Integrate machine learning for improved scoring and feedback quality
- Support cloud deployment and user accounts across devices
- Add audio coaching and voice feedback
- Introduce dashboards with historical charts and trends
- Expand the system to support more sports and advanced drills
- Improve security and production deployment architecture

---

## 20. Conclusion

PocketCoach AI is a technically rich and practically useful project that combines modern web development, computer vision, and AI-driven coaching concepts. It demonstrates how a browser-based system can analyze human movement in real time and provide meaningful feedback to users. The project brings together multiple disciplines including software engineering, application design, data modeling, API design, and intelligent systems.

The implementation successfully demonstrates a complete flow from user authentication to live pose analysis and training feedback. It is a strong example of how software can be used to create personalized, accessible, and intelligent sports coaching experiences.

---

## 21. How to Use This Report

This report can be used as a formal technical documentation file for submission to a professor or academic supervisor. It can also be exported to PDF from Markdown using any standard editor or conversion tool.

Suggested export steps:
1. Open the file in VS Code
2. Use the Print option or export as PDF if available
3. Alternatively, use a Markdown-to-PDF converter if needed

---

## 22. Project Summary in One Paragraph

PocketCoach AI is an AI-powered sports coaching platform that uses webcam-based pose detection and analysis to provide real-time technique feedback for athletes. Built with a FastAPI backend, SQLAlchemy database, and a vanilla JavaScript frontend, the system supports user authentication, session tracking, skill guidance, and sport-specific feedback. Its modular architecture makes it extensible for multiple sports and future AI enhancements, making it a strong example of an integrated full-stack intelligent application.
