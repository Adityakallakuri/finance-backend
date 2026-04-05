Finance Backend API

Overview
This project is a backend system built using Flask to manage financial data such as income and expenses. It allows users to create accounts, log in securely, and access features based on their roles. The system also provides useful financial insights like total income, expenses, and trends.

What this project does
This backend allows users to register and log in using secure authentication. It uses JWT tokens to manage user sessions. Based on the role of the user (admin, analyst, or viewer), different levels of access are provided. Users can create, view, update, and delete financial records. The system also generates dashboard data such as totals, category-wise summaries, and monthly trends. Proper validation and error handling are implemented to ensure correct data processing.

Technologies Used
Flask is used as the backend framework.
SQLite is used as the database.
JWT is used for authentication.
Postman is used for testing APIs.

Project Structure
The project is organized into different parts such as routes, models, and middleware. Routes handle API requests, models manage database operations, and middleware takes care of authentication and validation.

How to Run the Project
First, clone the repository from GitHub.
Then install the required dependencies using pip.
Finally, run the server using the Python command.

Authentication
After logging in, a token is generated. This token must be included in the request headers to access protected APIs.

API Endpoints
Authentication APIs include register, login, and getting user profile.
Record APIs include fetching records, creating new records, updating existing ones, and deleting records.
Dashboard API provides summary details such as total income, expenses, and trends.

Design Choices
Flask was chosen because it is simple and flexible for building APIs. SQLite was used for easy setup and quick development. JWT was used to maintain secure and stateless authentication. The code is structured in a modular way to make it easy to understand and maintain.

Limitations
The project uses SQLite, which is not suitable for large-scale production systems. There is no frontend interface, as this is a backend-only project. The application is not deployed and runs locally.

Future Improvements
The project can be improved by adding a frontend interface, deploying it to a cloud platform, using a more scalable database like PostgreSQL, and enhancing security features.

Final Note
This project demonstrates how a backend system works with authentication, role-based access control, data management, and analytics. It covers all the core concepts required for building a real-world backend application.

Status
Completed and ready for submission.
