from flask import Flask, g, render_template
import sqlite3
app = Flask(__name__)

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv



@app.route("/")
def home():
    return render_template("Boxing.html")







@app.route("/weight/<int:id>")
def weight(id):
    boxers = query_db("SELECT * FROM Boxer WHERE Weight_ID = ?", (id,))


    division_title = {
        1: "Lightweight Division",
        2: "Middleweight Division",
        3: "Heavyweight Division"
    }

    division_title = division_title.get(id, "Boxing Divisions")

    total_fighters = len(boxers)

    total_wins = 0
    total_losses = 0

    for boxer in boxers:
        total_wins = total_wins + boxer[5]
        total_losses = total_losses + boxer[6]
    
    if boxers:
        top_fighter = max(boxers, key=lambda boxer: boxer[5])
    else:
        top_fighter = None

    undefeated_boxers = []

    for boxer in boxers:
        if boxer[6] == 0:
            undefeated_boxers.append(boxer)

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


@app.route("/fighter/<int:id>")
def fighter(id):
    boxers = query_db("SELECT * FROM Boxer")

    boxer = None

    for current_boxer in boxers:
        if int(current_boxer[0]) == id:
            boxer = current_boxer
            break

    if boxer is None:
        return "Fighter not found", 404

    return render_template("fighter.html", boxer=boxer)    
if __name__ == "__main__":
    app.run(debug=True)
