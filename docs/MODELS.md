# Database Models Documentation

This document outlines the database structure for the Edify platform. The application uses SQLAlchemy as its Object-Relational Mapping (ORM) system, with Flask-SQLAlchemy for Flask integration.

All models are located in the [`edify/models/`](../edify/models/) directory.

## Model Architecture

### Base Model Structure

The base model structure is defined in [`base.py`](../edify/models/base.py). All models inherit from `BaseModel`, which provides common functionality:

- `__repr__`: This method is intended to return a string representation of the model instance, which is useful for debugging and logging purposes.

- `to_dict`: This method converts the model instance into a dictionary format. It can take an optional parameter `simplified` to determine whether to include all attributes or just a subset of them.

Additionally, there is a static method `to_dict_all` that takes a list of model instances and converts each one into a dictionary, facilitating the conversion of multiple objects at once.

### Core Models

#### 1. User Model

[`user.py`](../edify/models/user.py)

- Handles user authentication and profile information
- Supports multiple authentication levels
- Includes language preferences

#### 2. Academic Models

[`academic.py`](../edify/models/academic.py)

- **School**: Educational institutions
- **Major**: Fields of study
- **Course**: Individual courses
- **AcademicField**: Broader academic categories

#### 3. Question Model

[`question.py`](../edify/models/question.py)

- Represents tutoring requests
- Includes scheduling and method preferences
- Links to academic information

#### 4. Offer Model

[`offer.py`](../edify/models/offer.py)

- Represents tutor responses to questions
- Tracks offer status and negotiations
- Manages pricing and scheduling

#### 5. Notification Model

[`notification.py`](../edify/models/notification.py)

- Handles system notifications
- Supports different notification types
- Manages user alerts and updates

## Database Migrations

When modifying database models, follow these steps to ensure proper migration:

   <ol>
       <li>Get database to latest version: <code>flask db upgrade</code>
       </li>
       <li>Generate migration for model changes: <code>flask db migrate</code>
       </li>
       <li>Apply new migration: <code>flask db upgrade</code>
       </li>
       <li>Test downgrade functionality: <code>flask db downgrade</code>
       </li>
       <li>Fix any downgrade script issues if needed by manually editing the downgrade function in the migration file</li>
       <li>Verify upgrade works after downgrade: <code>flask db upgrade</code>
       </li>
   </ol>

**Always test that both upgrade and downgrade operations work correctly before committing or pushing changes.** This ensures database changes can be safely rolled back if needed.
