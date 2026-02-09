# Connect 👋

A Flask-based social web application built for the M.Sc. batch (2020–2022) of NIT Tiruchirappalli (NITT). Batch members can connect, share posts/memes, browse a photo gallery of memories, and view alumni profiles scraped from LinkedIn.

## Features

- **Memes / Posts Feed** — Authenticated users can create, update, and delete posts with optional image/GIF/MP4 attachments. All posts are displayed on the home page with author profile picture, username, and date.
- **Meet Us (Alumni Directory)** — Displays alumni profile cards in a column grid (name, photo, job title, location, about section, LinkedIn contact link) sourced from `linkedinScrapped.csv`.
- **Memories Gallery** — A photo gallery of batch memory images arranged in rows, each with a Bootstrap modal for full-size viewing. Includes a glowing animated "Memories" heading.
- **User Authentication** — Register, login, logout with bcrypt password hashing. Session management via Flask-Login with `login_view` redirect to the login page.
- **Account Management** — Update username, email, and profile picture. Uploaded profile pictures are resized to 125×125 using Pillow and saved with a random hex filename.
- **Sidebar Widgets** — Embedded NIT Trichy Facebook page timeline, Twitter/X feed, a timeanddate.com clock widget, and a YouTube video modal (triggered by clicking a thumbnail in the sidebar).
- **Navbar Links** — Discord server invite, WhatsApp contact link, and a link to an external farewell party page (`rakesh-bairwa.github.io/farwell`).
- **Video Background** — Full-screen looping muted `background.mp4` video fixed behind all page content.

## Tech Stack

| Layer      | Technology                                       |
|------------|--------------------------------------------------|
| Backend    | Python 3, Flask                                  |
| Database   | SQLite (via Flask-SQLAlchemy)                     |
| Auth       | Flask-Login, Flask-Bcrypt                         |
| Forms      | Flask-WTF, WTForms, email-validator               |
| Frontend   | Jinja2 templates, Bootstrap 4.0, custom CSS       |
| Scraper    | Selenium (Firefox/geckodriver), BeautifulSoup, requests, pandas |
| Image      | Pillow (resize profile pics)                      |

## Project Structure

```
Connect-main/
├── main.py                  # App entry point — imports app from project, runs Flask dev server (debug=False)
├── linkedin.py              # LinkedIn profile scraper (fully commented out, already executed)
├── linkedinScrapped.csv     # 49 alumni records: Full Name, Image, Title, Location, About, Contact
├── requirements.txt         # Python dependencies for the web app
├── ReadMe.txt               # Original readme notes
├── README.md                # This file
└── project/
    ├── __init__.py          # App factory — creates Flask app, configures SQLAlchemy, Bcrypt, LoginManager
    ├── models.py            # SQLAlchemy models: User and Post, plus db.create_all() at module level
    ├── forms.py             # WTForms: RegistrationForm, LoginForm, UpdateAccountForm, PostForm
    ├── routes.py            # All 11 route handlers + CSV loading at module level
    ├── site.db              # SQLite database file (auto-created by db.create_all())
    ├── static/
    │   ├── main.css         # Custom styles — navbar (.bg-steel), cards, video bg, glow animation, responsive columns
    │   ├── background.mp4   # Full-screen looping background video (~17 MB)
    │   ├── shortflim.mp4    # Short film video asset (~17 MB, not directly used — YouTube embed used instead)
    │   ├── profile_pics/    # User profile pictures & post image uploads (default.jpg included)
    │   └── seniors/         # 52 files: 50 numbered batch photos (1–50.jpeg), play.jpeg, amit_senior_website.jpg
    └── templates/
        ├── layout.html      # Base template — navbar, sidebar widgets, video bg, Bootstrap 4, modals, flash messages
        ├── home.html        # Post feed — iterates all posts showing author avatar, name, date, title, content, image
        ├── about.html       # Alumni directory — 3-column card grid from CSV data with scrollable about sections
        ├── memories.html    # Photo gallery — 48 images in rows of 3 with 50 Bootstrap modals for full-size view
        ├── register.html    # Registration form — username, email, password, confirm password with validation errors
        ├── login.html       # Login form — email, password, remember me checkbox, forgot password link (non-functional)
        ├── account.html     # Account settings — displays current avatar, update username/email/profile picture
        ├── create_post.html # Reusable form for both create & update post (legend passed as template variable)
        └── post.html        # Single post view — shows post with update/delete buttons (author only) + delete confirmation modal
```

## Detailed File Breakdown

### `main.py`
Entry point. Imports the `app` object from the `project` package and runs the Flask development server with `debug=False`.

### `project/__init__.py`
App factory (without factory pattern — uses a global `app` object):
- Creates the Flask app and SQLite database URI (`sqlite:///site.db`)
- Initializes `SQLAlchemy`, `Bcrypt`, and `LoginManager` extensions
- Sets `login_manager.login_view = 'login'` so unauthenticated users are redirected to `/login`
- Sets `login_manager.login_message_category = 'info'` for Bootstrap-styled flash messages
- Imports `routes` at the bottom to avoid circular imports

### `project/models.py`
Defines two SQLAlchemy models:

**User**
| Column       | Type          | Constraints                    |
|-------------|---------------|--------------------------------|
| `id`        | Integer       | Primary key                    |
| `username`  | String(20)    | Unique, not null               |
| `email`     | String(120)   | Unique, not null               |
| `password`  | String(60)    | Not null (bcrypt hash)         |
| `image_file`| String(20)    | Not null, default `default.jpg`|
| `posts`     | Relationship  | Backref `author`, lazy=True    |

**Post**
| Column       | Type          | Constraints                    |
|-------------|---------------|--------------------------------|
| `id`        | Integer       | Primary key                    |
| `title`     | String(100)   | Not null                       |
| `date_posted`| DateTime     | Not null, default `datetime.utcnow` |
| `content`   | Text          | Not null                       |
| `img_path`  | String(500)   | Nullable (optional image URL)  |
| `user_id`   | Integer       | Foreign key → `user.id`, not null |

Also includes `load_user` callback for Flask-Login and calls `db.create_all()` at module level to auto-create tables.

### `project/forms.py`
Four WTForms form classes:

- **RegistrationForm** — `username` (2–20 chars), `email`, `password`, `confirm_password` (must match). Custom validators check for duplicate username/email in the database.
- **LoginForm** — `email`, `password`, `remember` (BooleanField).
- **UpdateAccountForm** — `username`, `email`, `picture` (FileField, allows jpg/png/jpeg). Custom validators skip uniqueness check if the value hasn't changed from `current_user`.
- **PostForm** — `title`, `content` (TextAreaField), `picture` (allows jpg/png/jpeg/gif/mp4).

### `project/routes.py`
Loads `linkedinScrapped.csv` into a list at module level (runs once on startup). Defines 11 route handlers:

| Route                    | Function       | Key Behavior |
|--------------------------|---------------|--------------|
| `GET /`                  | `home()`       | Queries all posts via `Post.query.all()`, flashes login prompt if unauthenticated |
| `GET /meet_us`           | `about()`      | Passes CSV data + length to `about.html` for column card rendering |
| `GET /memories`          | `memories()`   | Renders static gallery page |
| `GET,POST /register`     | `register()`   | Redirects if already logged in; hashes password with bcrypt; creates User; redirects to login |
| `GET,POST /login`        | `login()`      | Redirects if already logged in; verifies bcrypt hash; supports `next` query param redirect |
| `GET /logout`            | `logout()`     | Calls `logout_user()`, redirects to home |
| `GET,POST /account`      | `account()`    | `@login_required`. Pre-fills form on GET. On POST: resizes uploaded picture to 125×125, saves with random hex name, updates user in DB |
| `GET,POST /post/new`     | `new_post()`   | `@login_required` is **commented out**. Saves uploaded image at full resolution (no resize). Creates Post linked to `current_user` |
| `GET /post/<id>`         | `post()`       | Returns 404 if post not found |
| `GET,POST /post/<id>/update` | `update_post()` | `@login_required`. Returns 403 if not the author. Pre-fills form on GET. **Note:** clears `img_path` to None if no new image is uploaded during update |
| `POST /post/<id>/delete` | `delete_post()` | `@login_required`. Returns 403 if not the author. Deletes post from DB (does not delete the image file from disk) |

### `project/templates/layout.html`
Base Jinja2 template extended by all pages:
- Bootstrap 4.0 CSS/JS via CDN (jQuery 3.2.1, Popper.js 1.12.9)
- Full-screen fixed `<video>` background (autoplay, muted, loop)
- Responsive navbar branded "Let's Connect 👋" with links: Memes, Memories, Meet us, Discord, WhatsApp, Farewell party
- Conditional navbar: shows New Post / Account / Logout when authenticated, Login / Register when not
- Flash message rendering with Bootstrap alert categories
- 8-column main content area + 4-column sidebar with:
  - `play.jpeg` thumbnail → opens YouTube video modal (`fUfbL8G_l4g`)
  - timeanddate.com clock widget (Kolkata timezone)
  - NIT Trichy Facebook page plugin (timeline tab)
  - Twitter/X embedded timeline for `@ReachNITT`

### `project/templates/about.html`
Iterates over CSV data in steps of 3 to render a 3-column card layout. Each card shows: profile image, "Contact" button (links to LinkedIn), name, job title, location, and about section in a scrollable div. Has a minor HTML typo (`<p">` instead of `<p>`).

### `project/templates/memories.html`
Statically lists 48 batch photos in rows of 3 with varying heights (135px–400px). Each image triggers a Bootstrap modal for full-size viewing. Includes a CSS glow-animated "Memories" heading and a subtitle "From the Batch 2020-2022". Contains 50 modal definitions.

### `project/templates/create_post.html`
Reusable form template for both creating and updating posts. Receives a `legend` variable ("New Post" or "Update Post") to change the heading. Supports `enctype="multipart/form-data"` for file uploads.

### `project/templates/post.html`
Single post view. Shows author avatar, username, date, title, content, and optional image. If the current user is the author, displays "Update Post" and "Delete Post" buttons. Delete triggers a Bootstrap confirmation modal with a POST form.

### `project/static/main.css`
Custom styles including:
- `.bg-steel` — dark teal navbar (`#004445`)
- `.content-section` — white card with border and rounded corners
- `.article-*` — post feed styling (title, metadata, content, circular avatar)
- `.account-img` — 125×125 circular profile picture
- `.column` / `.card` — 3-column responsive grid for alumni cards (collapses to single column below 650px)
- `.scrollable` — overflow-y auto with 300px max height for alumni about sections
- `.button` — full-width black contact button with hover effect
- `#myVideo` — fixed full-screen video background
- `.glow` — CSS keyframe animation for glowing text effect on the memories page heading (white/teal text-shadow pulse)

### `linkedin.py`
Scraper that was used to populate `linkedinScrapped.csv`:
1. Searches Google (10 pages) for LinkedIn profiles matching NIT Trichy + Statistics + Computer Science
2. Extracts LinkedIn URLs from Google search results using a custom `extract_link()` parser
3. Logs into LinkedIn via Selenium (Firefox with geckodriver)
4. For each profile: scrolls the page, then scrapes name (`h1` in `ph5 pb5` div), profile image URL, job title (via `html2text`), location, and about section using BeautifulSoup
5. Handles errors per-profile with try/except (skips failures)
6. Saves all data to `result.csv` using pandas DataFrame

### `linkedinScrapped.csv`
CSV with alumni records and 6 columns: `Full Name`, `Image`, `Title`, `Location`, `About`, `Contact`. Image URLs are mostly LinkedIn CDN links; one entry uses a local path (`/static/seniors/amit_senior_website.jpg`). Some fields are empty where scraping failed.

## Routes Summary

| Route                          | Method(s)    | Auth Required | Description                        |
|--------------------------------|-------------|---------------|------------------------------------|
| `/`                            | GET          | No            | Home page — displays all posts     |
| `/meet_us`                     | GET          | No            | Alumni directory from LinkedIn data|
| `/memories`                    | GET          | No            | Batch photo gallery                |
| `/register`                    | GET, POST    | No            | User registration                  |
| `/login`                       | GET, POST    | No            | User login                         |
| `/logout`                      | GET          | Yes           | Logout                             |
| `/account`                     | GET, POST    | Yes           | View/update profile                |
| `/post/new`                    | GET, POST    | No*           | Create a new post                  |
| `/post/<id>`                   | GET          | No            | View a single post                 |
| `/post/<id>/update`            | GET, POST    | Yes           | Update own post                    |
| `/post/<id>/delete`            | POST         | Yes           | Delete own post                    |

*`@login_required` is commented out on the new post route — any visitor can create posts if they are logged in (uses `current_user` as author).

## Setup & Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd Connect-main
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```
   The app will start at `http://127.0.0.1:5000`.

## Dependencies

**Web app** (`requirements.txt`):
- flask
- flask-login
- flask-sqlalchemy
- email_validator
- Pillow
- flask-bcrypt
- flask-wtf

**Scraper** (additional, only needed to re-run `linkedin.py`):
- pandas
- html2text
- requests
- beautifulsoup4
- selenium (+ Firefox + geckodriver)
