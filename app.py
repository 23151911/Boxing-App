"""Flask application for the boxing statistics website."""
import sqlite3
from flask import Flask, g, render_template, request, abort
app = Flask(__name__)

DATABASE = 'database.db'

#Create a connection to the database if one does not already exist
def get_db():
    """Create or return the current databse connection."""
    db = getattr(g, '_database', None)

    # Only create a new connection when there is no active connection
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# Close the database connection when flask finishes a request
@app.teardown_appcontext
def close_connection(_exception):
    """Close the database conection after each request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#Run SQL queries through one reusable function instead od repeating database code
def query_db(query, args=(), one=False):
    """Run an SQLite query and return the requested records."""
    # Execute the query, collect the results, then close the cursor
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# load the main homepage when the user visits the root URL
@app.route("/")
def home():
    """Display the homepage."""
    return render_template("Boxing.html")







@app.route("/weight/<int:weight_id>")
def weight(weight_id):
    """Display boxers from the selected weight division."""
    # Get only the boxers that belong to the selected weight divivison
    boxers = query_db(
        """
        SELECT Boxer_ID , CountryID, Name, Nickname, DateOfBirth, Wins,
        Losses, Weight_ID , File_name, Height_cm, Reach_cm, Stance, Style
        FROM Boxer WHERE Weight_ID = ?
        """,
        (weight_id,)
    )

    # Match each Weight_id to the division name shown on the page
    division_title = {
        1: "Lightweight Division",
        2: "Middleweight Division",
        3: "Heavyweight Division"
    }

    division_title = division_title.get(weight_id, "Boxing Divisions")

    total_fighters = len(boxers)
    # calculated the combined wins and losses for all fighters in the division
    total_wins = 0
    total_losses = 0

    for boxer in boxers:
        total_wins = total_wins + boxer[5]
        total_losses = total_losses + boxer[6]
    # Find the fighter with the highest number of wins if the division has fighter
    if boxers:
        top_fighter = max(boxers, key=lambda boxer: boxer[5])
    else:
        top_fighter = None
    # Create a separate list containing fighters that have never lost
    undefeated_boxers = []

    for boxer in boxers:
        if boxer[6] == 0:
            undefeated_boxers.append(boxer)
    # Send the division data and calcualted statistics to the HTML template
    return render_template(
        "weight.html",
        boxers=boxers,
        total_fighters=total_fighters,
        total_wins=total_wins,
        total_losses=total_losses,
        top_fighter=top_fighter,
        undefeated_boxers=undefeated_boxers,
        division_title=division_title
    )


@app.route("/fighter/<int:fighter_id>")
def fighter(fighter_id):
    """Display information for the selected boxer."""
    # Load boxer records so the requested fighter can be found by ID
    boxers = query_db(
    """
    SELECT Boxer_ID , CountryID, Name, Nickname, DateOfBirth, Wins,
    Losses, Weight_ID , File_name, Height_cm, Reach_cm, Stance, Style
    FROM Boxer
    """
    )



    boxer = None
    # Search through the records until the boxerwith the matching ID is found
    for current_boxer in boxers:
        if int(current_boxer[0]) == fighter_id:
            boxer = current_boxer
            break
    # Send invaild fighter IDs to the custom 404 erreo page
    if boxer is None:
        abort(404)
    # Retrieve only the achievements that belong to the selected Fighter
    achievements = query_db(
        """
        SELECT AchivementsID, BoxerID, Title, Year, Description
        FROM Achievements
        WHERE BoxerID = ?
        """,
        (fighter_id,)
    )

    return render_template(
        "fighter.html",
        boxer=boxer,
        achievements=achievements
    )



@app.route("/top-tier")
def top_tier():
    """Display the top-ranked boxers from each division."""
    # Load the boxer data used to build the TopTier ranking cards
    all_boxers = query_db(
        """
        SELECT Boxer_ID , CountryID, Name, Nickname, DateOfBirth, Wins, Losses,
        Weight_ID , File_name, Height_cm, Reach_cm, Stance, Style
        FROM Boxer
        """
    )

    # Store boxers by their ID so rankings records can be matched efficiently
    boxer_by_id = {}

    for boxer in all_boxers:
        boxer_by_id[int(boxer[0])] = boxer
    # Retrieve the rankings sepretely for each weight division
    lightweight_rankings = query_db(
        """
        SELECT RankingsID, BoxerID, Weight_ID, Rank, Points, LastUpdated
        FROM Rankings
        WHERE Weight_ID = 1
        ORDER BY Rank
        """
    )

    middleweight_rankings = query_db(
        """
        SELECT RankingsID, BoxerID, Weight_ID, Rank, Points, LastUpdated
        FROM Rankings
        WHERE Weight_ID = 2
        ORDER BY Rank
        """
        )
    heavyweight_rankings = query_db(
        """
        SELECT RankingsID, BoxerID, Weight_ID, Rank, Points, LastUpdated
        FROM Rankings
        WHERE Weight_ID = 3
        ORDER BY Rank
        """
        )

    # Create lists that will hold the ranked boxer records for each division
    lightweight = []
    middleweight = []
    heavyweight = []
    # Match each lightweight rankings records to its boxer information
    for rankings in lightweight_rankings:
        boxer_id = int(rankings[1])

        if boxer_id in boxer_by_id:
            lightweight.append(boxer_by_id[boxer_id])

     # Match each middleweight rankings records to its boxer information
    for rankings in middleweight_rankings:
        boxer_id = int(rankings[1])

        if boxer_id in boxer_by_id:
            middleweight.append(boxer_by_id[boxer_id])

     # Match each heavyweight rankings records to its boxer information
    for rankings in heavyweight_rankings:
        boxer_id = int(rankings[1])

        if boxer_id in boxer_by_id:
            heavyweight.append(boxer_by_id[boxer_id])

    return render_template(
        "top-tier.html",
        lightweight=lightweight,
        middleweight=middleweight,
        heavyweight=heavyweight
    )

@app.route("/search")
def search():
    """Search for boxers using full or partial names."""
    # Get the search text entered by the user and remove extra spaces
    search_text = request.args.get("q", "").strip()
    # Show an empty results page if the user submits a blank search
    if search_text == "":
        return render_template(
            "search.html",
            boxers=[],
            search_text=""
        )
    # Use a parameterised LIKE query to find full or partial boxer names
    boxers = query_db(
        """
        SELECT Boxer_ID , CountryID, Name, Nickname, DateOfBirth, Wins,
        Losses, Weight_ID , File_name, Height_cm, Reach_cm, Stance, Style
        FROM Boxer
        WHERE Name LIKE ?
        ORDER BY NAME
        """,
        ("%" + search_text + "%",)
    )
    # Send the matching boxer records and search text to the results page
    return render_template(
        "search.html",
        boxers=boxers,
        search_text=search_text
    )
# Display the custom 404 page when a requested page cannot be found
@app.errorhandler(404)
def page_not_found(_error):
    """Display a custom page when the requested page does not exist."""
    return render_template("404.html"), 404
# Start the Flask development server when this file is run directly
if __name__ == "__main__":
    app.run(debug=True)
