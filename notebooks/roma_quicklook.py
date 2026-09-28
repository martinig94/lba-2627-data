"""Quick look at the two Rome teams vs the league. Run after at least one collection:

    python notebooks/roma_quicklook.py
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
ROMA = ["BC Roma", "Maxima Roma"]

games = pd.read_csv(DATA / "games.csv")
box = pd.read_csv(DATA / "box_scores.csv")
pbp = pd.read_csv(DATA / "pbp.csv")

played = games[games.game_status == 2]
print(f"{len(played)} games played of {len(games)}\n")

# --- team level: four factors from the `total` rows -----------------------------------------
tot = box[box.row_type == "total"].copy()
tot["fga"] = tot.fg2a + tot.fg3a
tot["fgm"] = tot.fg2m + tot.fg3m
opp = tot[["game_id", "team_id", "oreb", "dreb", "pts"]].rename(
    columns={"team_id": "opponent_id", "oreb": "opp_oreb", "dreb": "opp_dreb", "pts": "opp_pts"})
tot = tot.merge(opp, on=["game_id", "opponent_id"])
tot["poss"] = tot.fga - tot.oreb + tot.tov + 0.44 * tot.fta
tot["ortg"] = 100 * tot.pts / tot.poss
tot["drtg"] = 100 * tot.opp_pts / tot.poss
tot["efg"] = (tot.fgm + 0.5 * tot.fg3m) / tot.fga
tot["tov_pct"] = tot.tov / tot.poss
tot["oreb_pct"] = tot.oreb / (tot.oreb + tot.opp_dreb)
tot["ftr"] = tot.fta / tot.fga
team = tot.groupby("team")[["ortg", "drtg", "efg", "tov_pct", "oreb_pct", "ftr", "poss"]].mean()
team["net"] = team.ortg - team.drtg
print("Team four factors (per-game means), league sorted by net rating:")
print(team.sort_values("net", ascending=False).round(3).to_string(), "\n")

# --- player level for the Rome teams -------------------------------------------------------
pl = box[(box.row_type == "player") & box.team.isin(ROMA) & (box.sec > 0)].copy()
pl["mp"] = pl.sec / 60
per = pl.groupby(["team", "player_surname"]).agg(
    g=("game_id", "nunique"), mpg=("mp", "mean"), pts=("pts", "mean"), reb=("reb", "mean"),
    ast=("ast", "mean"), val=("val", "mean"), pm=("plus_minus", "mean"),
    fg3m=("fg3m", "sum"), fg3a=("fg3a", "sum"))
per["fg3_pct"] = per.fg3m / per.fg3a.replace(0, pd.NA)
print("Rome teams, per-game player averages:")
print(per.sort_values(["team", "mpg"], ascending=[True, False]).round(2).to_string(), "\n")

# --- shot profile from play-by-play --------------------------------------------------------
shots = pbp[pbp.event.str.contains(r"^\d punti", regex=True, na=False) & pbp.team.isin(ROMA)].copy()
shots["made"] = shots.event.str.contains("segnato")
shots["three"] = shots.event.str.startswith("3")
prof = shots.groupby(["team", "qualifier_1"]).agg(att=("made", "size"), made=("made", "sum"))
prof["pct"] = prof.made / prof.att
print("Rome teams, shot attempts by shot type (pbp qualifier):")
print(prof.sort_values(["team", "att"], ascending=[True, False]).round(3).to_string())
