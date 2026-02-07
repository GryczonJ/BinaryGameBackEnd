# API ENDPOINTS

## AUTH & USERS
- **POST**   /auth/register
- **POST**   /auth/login
- **POST**   /auth/logout
- **POST**   /auth/refresh-token
- **GET**    /auth/me

## USER PROFILE
- **GET**    /users/me
- **PATCH**  /users/me
- **GET**    /users/:id

## PUZZLES (core game)
- **GET**    /puzzles/story
- **GET**    /puzzles/story/:id
- **GET**    /puzzles/random
- **GET**    /puzzles/daily/today
- **GET**    /puzzles/daily/:date

## GAMEPLAY / SOLVES
- **POST**   /solves
- **GET**    /solves/me
- **GET**    /solves/puzzle/:puzzleId

## RANKINGS & STATS
- **GET**    /rankings/daily/:date
- **GET**    /rankings/daily/:date/top
- **GET**    /rankings/user/:userId

## CALENDAR
- **GET**    /calendar/daily

## AI HELP / HINTS
- **POST**   /ai/hint

## ADMIN (optional)
- **POST**   /admin/puzzles
- **PATCH**  /admin/puzzles/:id
- **DELETE** /admin/puzzles/:id
- **POST**   /admin/daily/:date

---

# DATABASE DIAGRAM (dbdiagram.io format)

## USERS
Table users {
  id uuid [pk]
  login varchar [unique, not null]
  email varchar [unique, not null]
  password_hash varchar [not null]
  nick varchar
  avatar_url varchar
  created_at timestamp
  last_login timestamp
}

## SESSIONS
Table sessions {
  id uuid [pk]
  user_id uuid [ref: > users.id]
  token varchar [unique, not null]
  created_at timestamp
  expires_at timestamp
}

## PUZZLES
Table puzzles {
  id uuid [pk]
  type varchar  // story | daily | random
  difficulty int
  size int
  grid_solution text
  grid_initial text
  created_at timestamp
}

## STORY PUZZLES
Table story_puzzles {
  id uuid [pk]
  puzzle_id uuid [ref: > puzzles.id]
  order_index int
}

## DAILY PUZZLES
Table daily_puzzles {
  date date [pk]
  puzzle_id uuid [ref: > puzzles.id]
}

## SOLVES
Table solves {
  id uuid [pk]
  user_id uuid [ref: > users.id]
  puzzle_id uuid [ref: > puzzles.id]
  time_seconds int
  mistakes int
  hints_used int
  completed bool
  created_at timestamp
}

## DAILY RANKINGS
Table daily_rankings {
  id uuid [pk]
  date date
  user_id uuid [ref: > users.id]
  rank int
  score int
  indexes {
    (date, user_id) [unique]
  }
}

## AI HINTS
Table ai_hints {
  id uuid [pk]
  user_id uuid [ref: > users.id]
  puzzle_id uuid [ref: > puzzles.id]
  hint_text text
  created_at timestamp
}

---

# RELATION SUMMARY
users
 ├─ solves
 ├─ daily_rankings
 └─ ai_hints

puzzles
 ├─ solves
 ├─ story_puzzles
 ├─ daily_puzzles
 └─ ai_hints
