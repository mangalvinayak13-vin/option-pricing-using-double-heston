"""The words and numbers every theme shares. One source, so all six themes say the same true things.

Copied from designs/gen/content.py (the design canvases) and maintained here for the website;
export.py turns it into assets/data/content.json. Numbers come from assets/data/site.json
(real NSE files, verified research outputs, the project's pricer) and ferro_pair.json.
Wording rules: plain language, sentence case, no ALL-CAPS labels, buttons say what they do.
"""
import json
import math
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[1] / "assets" / "data"
DATA = json.loads((_DATA_DIR / "site.json").read_text())
PAIR = json.loads((_DATA_DIR / "ferro_pair.json").read_text())


def inr(v, dp=2):
    """Indian digit grouping: 1,23,456.78."""
    neg = v < 0
    s = f"{abs(v):.{dp}f}"
    whole, _, frac = s.partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return ("-" if neg else "") + whole + ("." + frac if frac else "")


D = DATA
K = D["contract"]
HL = D["half_life"]
AMB = D["ambiguity_summary"]
CB = D["consolidated"]["classical_baseline"]
G8 = D["consolidated"]["g8"]
NET = D["consolidated"]["models"]["Model_2_canonical_latent"]
RATIO = D["ratio_to_random"]
RAND = D["random_pair_median"]
SHARE = AMB["share_with_multiple_equivalents"]
FLAT_BETTER = 1 - D["dh_over_flat_median"]
SPOT = K["spot"]
LAST_DAY = "25 Sep 2026"
FIRST_DAY = "1 Jul 2026"
N_DAYS = D["days"][2]
EXPIRY = "27 Oct 2026"
PER = D["per_param"]
NB = {p["name"]: p["near_bound"] for p in PER}

WATCH = D["watch"]
NAMES = {"NIFTY 50": "Index", "NIFTY BANK": "Index", "RELIANCE": "Reliance Industries", "HDFCBANK": "HDFC Bank",
         "INFY": "Infosys", "TCS": "Tata Consultancy", "ICICIBANK": "ICICI Bank", "SBIN": "State Bank of India",
         "ITC": "ITC", "LT": "Larsen & Toubro", "BHARTIARTL": "Bharti Airtel", "KOTAKBANK": "Kotak Mahindra Bank",
         "BAJFINANCE": "Bajaj Finance", "MARUTI": "Maruti Suzuki", "HCLTECH": "HCL Technologies", "WIPRO": "Wipro",
         "TATASTEEL": "Tata Steel", "ONGC": "ONGC", "COALINDIA": "Coal India", "HINDUNILVR": "Hindustan Unilever"}


def w(sym):
    return next(x for x in WATCH if x["sym"] == sym)


FEATURED = ["NIFTY 50", "NIFTY BANK", "RELIANCE", "HDFCBANK", "INFY", "TCS", "ICICIBANK", "SBIN", "ITC", "LT"]
REL = D["equity"]["RELIANCE"]  # [date, o, h, l, c, vol, prev]


def short_date(d):  # 2026-09-25 -> 25 Sep
    m = {"07": "Jul", "08": "Aug", "09": "Sep"}[d[5:7]]
    return f"{int(d[8:])} {m}"


REL_ROWS = [[short_date(r[0]), r[1], r[2], r[3], r[4], r[5]] for r in REL]
REL_LAST = REL[-1]

# ------------------------------------------------------------------ home -----------------
Q = "Does letting volatility move price options better?"
A_SHORT = "For fitting today's prices, yes."
A_LONG = ("Real option prices bend: protection against a fall usually costs more than a bet on a rise. "
          f"Double Heston bends the same way, and on all 2,400 real NSE option surfaces we tested, its best fit "
          f"beat one fixed volatility.")
TWIST = "Ask it which of its ten settings produced the bend, though, and the prices can't tell you."
SLOW = ("Slow factor", "κ 0.5", f"Half of any shock fades in {HL['slow_years']:.1f} years")
FAST = ("Fast factor", "κ 5.0", f"Half of any shock fades in about {HL['fast_days'] / 7:.0f} weeks")
TWO_CLOCKS = ("Each factor is a volatility that gets knocked around and drifts back to normal. One drifts back "
              "slowly, one quickly, which lets the model shape short- and long-dated options differently.")
FINDING_LINE = (f"On {SHARE * 100:.0f}% of 2,400 real NSE option surfaces, several different settings priced the "
                f"options equally well.")
FINDING_SUB = (f"They sat {RATIO:.1f} times further apart than two settings picked at random from the model's "
               "training data. The market pins down today's volatility; it can't tell how fast volatility returns to normal.")
SMILE_CAPTION = "Implied volatility by strike, 30 days to expiry, at the model's starting settings. Computed with the project's pricer."
CTA = {"model": "Price an option", "finding": "See the finding", "market": "Open the market"}

# ------------------------------------------------------------------ market ---------------
MARKET_TITLE = "Market"
MARKET_SUB = (f"Official NSE closing prices, {FIRST_DAY} to {LAST_DAY}, {N_DAYS} trading days. "
              "Live prices from Upstox are planned for the same places; this version shows the closes.")
STATUS = f"Prices as of the NSE close, {LAST_DAY}, 15:30 IST"
UNIVERSE = "NIFTY 50, NIFTY BANK and the 40 most traded F&O stocks: every stock we show an implied volatility for."

# ------------------------------------------------------------------ model ----------------
CONTRACT = f"NIFTY {inr(K['strike'], 0)} call"
CONTRACT_SUB = f"Expires {EXPIRY}, {K['dte']} days"
MODEL_EXPLAIN = (f"The starting settings assume 20% volatility. On {LAST_DAY} the market was pricing about "
                 f"{K['market_iv']:.1f}%, so the model charges more. Lower today's level (v₀) and the gap closes. "
                 "There's no fit button: the finding explains why a computer can't pick all ten settings for you.")
GAP = K["dh"] - K["market"]
MC_LINE = f"Monte Carlo check, 20,000 paths: ₹{inr(K['mc'])} ± {K['mc_se']:.2f}"
MODEL_SOURCE = (f"Option prices: NSE closing prices, {LAST_DAY}. Forward from NIFTY October futures "
                f"({inr(K['forward'])}). Rate: RBI 91-day T-bill, 15 Jul observation carried forward, as in the research.")
SLIDERS = [  # (factor, symbol, name, value, lo, hi)
    ("slow", "v₀", "today's variance", 0.02, 0.0005, 1.0), ("slow", "κ", "speed back to normal", 0.5, 0.1, 10.0),
    ("slow", "θ", "long-run variance", 0.02, 0.0005, 1.0), ("slow", "ξ", "volatility of volatility", 0.3, 0.05, 2.0),
    ("slow", "ρ", "price–volatility link", -0.7, -0.99, 0.99),
    ("fast", "v₀", "today's variance", 0.02, 0.0005, 1.0), ("fast", "κ", "speed back to normal", 5.0, 0.1, 10.0),
    ("fast", "θ", "long-run variance", 0.02, 0.0005, 1.0), ("fast", "ξ", "volatility of volatility", 0.5, 0.05, 2.0),
    ("fast", "ρ", "price–volatility link", -0.7, -0.99, 0.99),
]
FELLER = {"slow": "Feller condition fails: 2κθ = 0.02 is below ξ² = 0.09", "fast": "Feller condition fails: 2κθ = 0.20 is below ξ² = 0.25"}
FELLER_NOTE = ("Both factors can touch zero at these settings. The simulator uses full truncation, so prices stay valid.")
GREEKS = [("Delta", f"{K['delta']:.3f}", "per ₹1 move in NIFTY"), ("Gamma", f"{K['gamma']:.5f}", "change in delta per ₹1"),
          ("Vega", f"{K['vega']:.1f}", "₹ per volatility point"), ("Theta", f"{K['theta']:.2f}", "₹ per calendar day"),
          ("Rho", f"{K['rho']:.1f}", "₹ per rate point")]
CHAIN = [r for r in D["chain"] if abs(r["strike"] - K["strike"]) <= 250]

# ------------------------------------------------------------------ maths ----------------
MATHS_INTRO = ("Double Heston (Christoffersen, Heston and Jacobs, 2009) lets the stock's variance come from two "
               "independent sources. Each follows its own mean-reverting process with five settings, ten in all.")
EQ_PRICE = "dS = (r − q) S dt + √v₁ S dW₁ + √v₂ S dW₂"
EQ_VAR = "dvᵢ = κᵢ (θᵢ − vᵢ) dt + ξᵢ √vᵢ dZᵢ,   corr(dWᵢ, dZᵢ) = ρᵢ,   i = 1, 2"
EQ_FELLER = "2κᵢθᵢ > ξᵢ²"
EQ_CF = "φ(u) = φ₁(u) · φ₂(u)"
EQ_CALL = "C = e^(−rT) [ F·P₁ − K·P₂ ],   Pⱼ = ½ + (1/π) ∫₀^∞ Re[ e^(−iu·ln(K/F)) φⱼ(u) / (iu) ] du"
MATHS_STEPS = [
    ("Two variances, not one", "The stock's variance is v₁ + v₂. Each factor pulls back toward its long-run level θ at speed κ, is shaken by ξ, and moves with the price at correlation ρ. A negative ρ means falls come with rising volatility: that tilts the smile."),
    ("Independent factors multiply", "Because the two factors are independent, the model's characteristic function is the product of each factor's own. That's what keeps pricing fast."),
    ("Price by one integral", "The option price comes from inverting the characteristic function (Gil-Pelaez). The code uses the 'little trap' form (Albrecher et al., 2007), which avoids a branch-cut error in the 1993 formula at long maturities."),
    ("Check by simulation", "Monte Carlo prices the same option by simulating 20,000 paths with full-truncation Euler steps and antithetic pairs. The two methods agree within the simulation's standard error."),
    ("The Feller condition", "If 2κθ > ξ², a factor's variance never reaches zero. Real markets often break it; full truncation keeps the simulation valid when it does."),
]
LINEAGE = [("1973", "Black–Scholes", "one fixed volatility, 1 setting"), ("1993", "Heston", "volatility that moves, 5 settings"),
           ("2009", "Double Heston", "two moving factors, 10 settings")]

# ------------------------------------------------------------------ finding --------------
FIND_HEAD = "A perfect price fit is not the same as knowing the settings."
PROOF1_HEAD = "Simulated surfaces, where the right answer is known"
PROOF1 = (f"We generated {CB['surfaces_calibrated']} option surfaces from known settings and asked a classical optimizer "
          f"to find them again, from {CB['starts_per_surface']} starting points each. It matched the prices almost exactly: "
          f"a median price error of 9.16 × 10⁻⁸. The settings it found scored {CB['mean_median_skill']:.2f} on recovery, "
          "where 1.00 is what you'd get by always guessing the typical value, and lower is better.")
PROOF1_NUMS = [("9.16 × 10⁻⁸", "median price error"), (f"{CB['mean_median_skill']:.2f}", "recovery skill (1.00 = guessing)"),
               (f"{CB['price_equivalent_subset']['mean_median_skill']:.2f}", f"on the {CB['price_equivalent_subset']['n']} closest price fits")]
PROOF1_NET = (f"Our neural network (a standard ANN, which learns only from examples) reads the settings from prices and scores {NET['mean_skill']:.2f} on the RMSE-based "
              f"version of the same score, where the optimizer scores {CB['mean_skill']:.2f}. It does better by leaning "
              f"toward typical values; the one setting it reads well is today's level (v₀, {NET['param_skill']['v0_s']:.2f}).")
PROOF2_HEAD = "Real NSE surfaces, where no answer is assumed"
PROOF2 = (f"On 2,400 real surfaces (40 of NSE's most traded stocks over 60 days) we started the fit from 16 places each "
          f"time. On {SHARE * 100:.0f}% of them, more than one set of settings priced the options equally well, within 10% "
          f"of the best fit's price error. Those equally good fits sat a median {AMB['median_dispersion']:.2f} apart, "
          f"against {RAND:.2f} for two settings picked at random from the training data: {RATIO:.1f} times as far.")
PROOF2_NUMS = [(f"{SHARE * 100:.0f}%", "of 2,400 surfaces had several equally good fits"),
               (f"{RATIO:.1f}×", "further apart than two random parameter sets"),
               (f"{FLAT_BETTER * 100:.0f}%", "less price error than one flat volatility, median")]
PER_PARAM = ("Split by setting, the pattern is physical. Today's level (v₀) is pinned down: equally good fits agree on "
             "it more closely than random sets would. The speeds back to normal (κ) are not pinned down at all; the best "
             f"fit's speed sat at the edge of the allowed range on {NB['kappa_s'] * 100:.0f}% (slow) and "
             f"{NB['kappa_f'] * 100:.0f}% (fast) of surfaces.")
HELDOUT = (f"On 8 later dates it never saw, our ANN repriced options with a median error of "
           f"{G8['median_network_relative'] * 100:.1f}%, against {G8['median_best_fit_relative'] * 100:.1f}% for the best "
           f"possible fit: a gap of {G8['median_gap_pp']:.1f} points.")

# the option backtest (outputs/option_backtest/option_backtest_pairs.csv): ANN-read settings vs Black-Scholes
import pandas as _pd  # noqa: E402
_BT = _pd.read_csv(Path(__file__).resolve().parents[2] / "outputs" / "option_backtest" / "option_backtest_pairs.csv")
BT_PAIRS = len(_BT)
BT_SAME_DAY = float((_BT.err_fresh_dh < _BT.err_bs_same_day).mean())
BT_SAME_DAY_N = int((_BT.err_fresh_dh < _BT.err_bs_same_day).sum())
BT_NEXT_DAY = float((_BT.err_stale_dh < _BT.err_stale_bs).mean())
BACKTEST = (f"With the settings our ANN reads from each day's own quotes, Double Heston priced that day's options better "
            f"than a same-day Black–Scholes fit on {BT_SAME_DAY * 100:.1f}% of {BT_PAIRS:,} stock-days ({BT_SAME_DAY_N:,} of them). "
            f"Carried to the next day, its settings beat Black–Scholes carried forward on {BT_NEXT_DAY * 100:.1f}%.")
BEAT_BS_NUM = f"{BT_SAME_DAY * 100:.1f}%"

# the physics-informed networks (PINNs): experiments/nifty_multifactor_v4 and outputs/unified_v6
_RM = json.loads((Path(__file__).resolve().parents[2] / "outputs" / "unified_v6" / "finetune_real_summary.json").read_text())["NIFTY"]
PINN_NIFTY = {k: _RM["median_iv_rmse"][k] * 100 for k in ("ft_3", "dh_cold", "sh", "bs")}
PINN_NIFTY_BEST = _RM["dates_best"]["ft_3"]
PINN_NIFTY_SECONDS = (_RM["median_seconds"]["ft_3"], _RM["median_seconds"]["dh_cold"])
NN_HEAD = "Two kinds of network: an ANN and a PINN"
ANN_TEXT = ("Our ANN (a standard artificial neural network) learns to read the ten settings from prices purely from "
            "examples. It produced the settings behind the 210-stock studies on this site.")
PINN_TEXT = ("Our PINNs (physics-informed neural networks) are also trained on the model's own pricing equation, so their "
             "answers must obey the physics, not just match examples. The Double Heston PINN learned from exact prices plus "
             "the pricing equation at 18,000 points, and reproduces the exact pricer to 1.1 × 10⁻⁵ (about 0.1 volatility "
             "points) on 8,192 points it never saw. On 40 controlled test surfaces it beat a refitted one-factor Heston, which "
             "beat Black–Scholes, every time.")
PINN_MARKET = (f"On real NIFTY options (10 high-volatility days in April 2026, 1,750 held-out quotes) our physics-informed "
               f"calibrator priced with a median error of {PINN_NIFTY['ft_3']:.2f} volatility points, against "
               f"{PINN_NIFTY['bs']:.2f} for Black–Scholes and {PINN_NIFTY['dh_cold']:.2f} for a classical Double Heston fit, in "
               f"{PINN_NIFTY_SECONDS[0]:.1f} s instead of {PINN_NIFTY_SECONDS[1]:.0f} s. It was the best model on "
               f"{PINN_NIFTY_BEST} of the 10 days.")
REL_STOCK = D["per_stock"]["RELIANCE"]


def rel_line():
    import statistics
    dh = statistics.median(r[1] for r in REL_STOCK) * 100
    fl = statistics.median(r[2] for r in REL_STOCK) * 100
    ds = statistics.median(r[3] for r in REL_STOCK)
    return (f"RELIANCE, day by day: its best Double Heston fit beat a flat volatility on every one of its 60 days "
            f"(median price error {dh:.2f}% of the share price, against {fl:.2f}%). On the same days the equally good "
            f"fits sat a median {ds:.1f} apart.")


# ------------------------------------------------------------------ about ----------------
ABOUT_HEAD = "A B.Tech physics project about one question and an honest answer."
VIDEO_CAPTION = "A narrated overview of the model and the finding, made from the project report. [Video to be added]"
# The explainer video: put the file in website/assets/video/ and set its path here, e.g. "assets/video/explainer.mp4",
# then run python3 website/tools/export.py. Empty means not added yet (the slot says so; nothing is fetched).
VIDEO_SRC = ""
METHOD = [
    "Prices come from the characteristic-function formula and are checked against Monte Carlo simulation.",
    f"Research data: official NSE end-of-day files, 210 stocks, 60 trading days, 12,480 option surfaces. "
    "The site shows NSE closing prices; live Upstox prices are planned.",
    "Every real-market result was re-run after three pipeline bugs were found and fixed, and checked against a flat "
    "volatility, which a true best fit can never lose to.",
]
LIMITS = [
    "No jumps: the largest one-day moves are still underestimated.",
    "Dividends are supported but set to zero; one interest rate for every maturity.",
    "Prices are frictionless. Real trading crosses a bid–ask spread.",
    "End-of-day research data has closing prices only, no bid–ask quotes.",
    "A typical surface has 17 of the 20 target option slots quoted (between 10 and 20 on 80% of surfaces).",
]
ALSO = ("Whether EWMA or GARCH forecasts of next month's volatility beat simply assuming it looks like "
        "last month, tested walk-forward over 60 stocks and ten years.")

# ------------------------------------------------------------------ team -----------------
TEAM_HEAD = "The team"
TEAM_INTRO = "Built for [Event] at [College]. Replace each placeholder with the real name and what that person built."
TEAM = [("[Name]", "[Role: e.g. model and pricer]"), ("[Name]", "[Role: e.g. data pipeline]"),
        ("[Name]", "[Role: e.g. website and design]"), ("[Name]", "[Role: e.g. research and report]")]
SUPERVISOR = ("[Supervisor name]", "[Department], [College]")
THANKS = ["NSE, for the public end-of-day files the research uses.", "Upstox, whose market-data API we plan to use for live prices.",
          "The authors of NumPy, SciPy and pandas."]

# ------------------------------------------------------------------ references -----------
REFS = [
    ("Models", [
        ("Black, F. and Scholes, M. (1973)", "The pricing of options and corporate liabilities.", "Journal of Political Economy 81(3)."),
        ("Merton, R. C. (1973)", "Theory of rational option pricing.", "Bell Journal of Economics and Management Science 4(1)."),
        ("Heston, S. L. (1993)", "A closed-form solution for options with stochastic volatility with applications to bond and currency options.", "Review of Financial Studies 6(2)."),
        ("Christoffersen, P., Heston, S. and Jacobs, K. (2009)", "The shape and term structure of the index option smirk: why multifactor stochastic volatility models work so well.", "Management Science 55(12)."),
    ]),
    ("Numerical methods", [
        ("Gil-Pelaez, J. (1951)", "Note on the inversion theorem.", "Biometrika 38."),
        ("Feller, W. (1951)", "Two singular diffusion problems.", "Annals of Mathematics 54."),
        ("Albrecher, H., Mayer, P., Schoutens, W. and Tistaert, J. (2007)", "The little Heston trap.", "Wilmott Magazine."),
        ("Lord, R., Koekkoek, R. and van Dijk, D. (2010)", "A comparison of biased simulation schemes for stochastic volatility models.", "Quantitative Finance 10(2)."),
        ("Glasserman, P. (2003)", "Monte Carlo Methods in Financial Engineering.", "Springer."),
    ]),
    ("History", [
        ("Brown, R. (1828)", "A brief account of microscopical observations on the particles contained in the pollen of plants.", "Philosophical Magazine 4."),
        ("Bachelier, L. (1900)", "Théorie de la spéculation.", "Annales scientifiques de l'École normale supérieure 17."),
        ("Einstein, A. (1905)", "Über die von der molekularkinetischen Theorie der Wärme geforderte Bewegung von in ruhenden Flüssigkeiten suspendierten Teilchen.", "Annalen der Physik 17."),
        ("Wiener, N. (1923)", "Differential space.", "Journal of Mathematics and Physics 2."),
        ("Itô, K. (1944)", "Stochastic integral.", "Proceedings of the Imperial Academy, Tokyo 20."),
        ("Samuelson, P. A. (1965)", "Rational theory of warrant pricing.", "Industrial Management Review 6."),
        ("Rubinstein, M. (1994)", "Implied binomial trees.", "Journal of Finance 49(3)."),
    ]),
    ("Neural networks", [
        ("Raissi, M., Perdikaris, P. and Karniadakis, G. E. (2019)", "Physics-informed neural networks: a deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations.", "Journal of Computational Physics 378."),
    ]),
    ("Data and software", [
        ("National Stock Exchange of India", "Bhavcopy end-of-day files, cash market and F&O, July to September 2026.", "nseindia.com."),
        ("Reserve Bank of India", "91-day Treasury bill yields.", "rbi.org.in."),
        ("Upstox", "Market data API (quotes, candles, option chains).", "upstox.com/developer."),
        ("NumPy, SciPy, pandas", "Numerical and data libraries used by the pricer and the research.", "numpy.org, scipy.org, pandas.pydata.org."),
    ]),
]


# ------------------------------------------------------------------ website only ---------
SITE_NAME = "Double Heston"
PAGES = [  # (id, file, label, short description)
    ("home", "index.html", "Home", "the question and the answer"),
    ("market", "market.html", "Market", "real NSE prices"),
    ("model", "model.html", "The model", "price an option"),
    ("maths", "how-it-works.html", "How it works", "the equations"),
    ("finding", "finding.html", "The finding", "why a fit isn't an answer"),
    ("results", "results.html", "Results", "every number, explained"),
    ("about", "about.html", "About", "video, method, limits"),
    ("team", "team.html", "Team", "who built it"),
    ("references", "references.html", "References", "papers and data"),
]
REL_LINE = rel_line()
SLOW_HL = f"{HL['slow_years']:.1f} years"
FAST_HL = f"{HL['fast_days']:.0f} days"
TICKER_MODEL = [  # values the model itself produced, shown in the ticker next to NSE closes
    (f"Double Heston, NIFTY {inr(K['strike'], 0)} call", f"₹{inr(K['dh'])}"),
    ("Market close, same option", f"₹{inr(K['market'])}"),
    ("Monte Carlo check", f"₹{inr(K['mc'])} ± {K['mc_se']:.2f}"),
    ("Slow factor half-life", SLOW_HL),
    ("Fast factor half-life", FAST_HL),
    ("Surfaces with several equally good fits", f"{SHARE * 100:.0f}%"),
]

# One real surface fitted twice (ferro_pair.json: the research's own multi-start fit, re-run)
PA, PB = PAIR["a"], PAIR["b"]
PAIR_SPOT = PAIR["spot"]
PAIR_ERR = (PAIR["a_rmse"] * PAIR_SPOT, PAIR["b_rmse"] * PAIR_SPOT)
_T = PAIR["term"]


def _term(k, day):
    return _T[k][_T["days"].index(day)] * 100


def half_life(kappa):
    d = math.log(2) / kappa * 365
    return f"{d / 365:.1f} years" if d >= 300 else f"{d:.0f} days"


PAIR_GAP_1Y = _term("a", 365) - _term("b", 365)
PAIR_HEAD = "Same surface, different magnets."
PAIR_LEDE = (f"Here is Bharti Airtel's option surface at the close on 21 Aug 2026, fitted twice. Both fits miss the "
             f"market by ₹{PAIR_ERR[0]:.2f} an option on average. One says a volatility shock takes "
             f"{half_life(PA['kappa_s'])} to fade by half; the other says {half_life(PB['kappa_f'])} to "
             f"{half_life(PB['kappa_s'])}.")
PAIR_MAGNETS_HEAD = "Underneath, the ten settings look nothing alike."
PAIR_MAGNETS = ("Ferrofluid takes its shape from magnets you can't see, and different magnets can raise the same "
                "surface. Option prices are the surface; the model's ten settings are the magnets.")
PAIR_PART_HEAD = f"Where the market trades, they agree. A year out, they're {PAIR_GAP_1Y:.1f} points apart."
PAIR_PART = (f"That day Bharti Airtel had options expiring in 4 and 39 days, and both fits price them alike. Ask them "
             f"about a one-year option, which isn't traded, and fit A says {_term('a', 365):.1f}% volatility while "
             f"fit B says {_term('b', 365):.1f}%. The prices give no reason to prefer either.")
PAIR_TYPICAL = (f"This surface had {PAIR['equivalents']} equally good fits out of 16 starts, and their spread, "
                f"{PAIR['median_dispersion']:.2f}, is the median of all 2,400 surfaces. It's the typical case, not the worst.")
PAIR_NOTE = ("Spike height is each setting's size on its own scale. * pressed against the fit's upper search limit "
             "for that setting.")
PAIR_SIX = (f"Bharti Airtel, 21 Aug 2026: 16 starts, {PAIR['equivalents']} fits within 10% of the best price error. "
            "Each spike is one fit. Where they bunch, the prices pin the setting down; where they scatter, they don't.")

# the story the motion tells
BEND_HEAD = "One fixed volatility draws a flat line. Real prices bend."
BEND = ("Black–Scholes prices every strike at the same volatility, so its smile is flat. Double Heston's two moving "
        "volatilities, tied to the price by a negative ρ, make protection against falls dearer: the line bends.")
_SURF = D["surface"]
_S1M = _SURF["iv"][_SURF["days"].index(30)]
_S1Y = _SURF["iv"][_SURF["days"].index(365)]
SURFACE_NOTE = (f"Implied volatility at the starting settings, for every strike and expiry. Low strikes, the protection "
                f"against falls, carry the most. The tilt is steepest at short expiries: {_S1M[0]:.1f}% down to {_S1M[-1]:.1f}% "
                f"across strikes at one month, {_S1Y[0]:.1f}% to {_S1Y[-1]:.1f}% at one year. ≈ 0 marks options worth almost "
                "nothing, where no volatility can be read.")
SKEW_NOTE = ("The gap between protection against falls and bets on rises, in volatility points, shrinks as expiry gets "
             "further away.")
FAN_NOTE = (f"Sixty of the simulated one-year paths from 100, with the middle 50% and 90% of all paths shaded. "
            f"The same simulator checks the pricer: 20,000 paths price the NIFTY {inr(K['strike'], 0)} call at ₹{inr(K['mc'])} "
            f"± {K['mc_se']:.2f}, against ₹{inr(K['dh'])} from the formula.")
FACTORS_HEAD = "Two volatilities, one fast and one slow."
FACTORS = (f"Each factor gets knocked about and drifts back to its long-run level. The fast one (κ 5.0) loses half "
           f"of any shock in {FAST_HL}; the slow one (κ 0.5) takes {SLOW_HL}. Same kind of process, different clocks.")


# ------------------------------------------------------------------ home: from Einstein's random walk to Wall Street
JOURNEY_HEAD = "From a speck of pollen to Wall Street"
JOURNEY_LEDE = ("Option pricing grew out of physics. The same random jiggling that Einstein explained in 1905 became "
                "the way finance describes prices, and this project carries that line forward to today's NSE options.")
JOURNEY = [  # (year, who, what happened)
    ("1827", "Robert Brown", "Under a microscope, tiny particles from pollen grains jiggle in water without stopping. Nobody can say why."),
    ("1900", "Louis Bachelier", "Five years before Einstein, a Paris thesis models stock prices as a random walk and prices options with it."),
    ("1905", "Albert Einstein", "Explains the jiggling: water molecules kick the particles at random. The spread grows with the square root of time."),
    ("1923", "Norbert Wiener", "Turns Brownian motion into exact mathematics: the Wiener process."),
    ("1944", "Kiyosi Itô", "Invents calculus for random paths. Itô's lemma becomes the working tool of quantitative finance."),
    ("1965", "Paul Samuelson", "Prices follow geometric Brownian motion: the random walk applies to returns, so prices can't go negative."),
    ("1973", "Black, Scholes and Merton", "A formula for the fair price of an option, with one fixed volatility."),
    ("1987", "The crash", "After Black Monday, index options stop fitting one volatility. Protection against falls costs more: the smile appears."),
    ("1993", "Steven Heston", "Volatility gets its own random walk, and options still have a near-closed-form price."),
    ("2009", "Christoffersen, Heston and Jacobs", "Two volatility factors, one fast and one slow: Double Heston, ten settings."),
    ("2019", "Raissi, Perdikaris and Karniadakis", "Physics-informed neural networks: networks trained to obey the equations of physics."),
    ("2026", "This project", "Double Heston on real NSE options, priced with our own code and read with an ANN and PINNs."),
]
DONE_HEAD = "What we did"
DONE = [  # (what, detail)
    ("Built the pricer", f"Double Heston by its characteristic function, checked by a 20,000-path Monte Carlo simulation: ₹{inr(K['dh'])} against ₹{inr(K['mc'])} ± {K['mc_se']:.2f}."),
    ("Collected real data", "Official NSE end-of-day files for 210 stocks over 60 trading days: 12,480 real option surfaces."),
    ("Trained an ANN", "A standard neural network that reads the model's ten settings from prices, learned from examples."),
    ("Trained PINNs", "Physics-informed networks that also obey Double Heston's pricing equation; one reproduces the exact pricer to 1.1 × 10⁻⁵."),
    ("Asked the hard question", "On 2,400 real surfaces, fitted from 16 starts each: can the prices tell us the settings? On 99% of them, no."),
    ("Found and fixed three bugs", "Then re-ran every real-market result and checked each against a flat volatility, which a true best fit can never lose to."),
    ("Built this site", "Every price on it comes from the project's own pricer; every number from NSE files or the research outputs."),
]

# ------------------------------------------------------------------ home: PINN vs ANN, computed (tools/pinn_vs_ann.py)
_PA = json.loads((_DATA_DIR / "pinn_vs_ann.json").read_text())
PA_TEST = _PA["test"]
PA_HEAD = "What the physics buys: a PINN against an ANN"
PA_LEDE = (f"Two identical networks saw the same {_PA['setup']['data_points']} exact Double Heston prices. The ANN learned from "
           f"those prices alone. The PINN also had to obey the model's pricing equation at {_PA['setup']['collocation_points']:,} "
           "points and the option's payoff at expiry. Below, both price surfaces at today's volatility, drawn in 3D against the "
           "exact pricer.")
_NEG = lambda net: sum(1 for row in _PA["slice"][net] for v in row if v < -0.002)  # below zero by > 0.2% of the strike
_NPTS = len(_PA["slice"]["s"]) * len(_PA["slice"]["tau"])
PA_RESULT = (f"On 2,000 fresh points the PINN's error was {PA_TEST['pinn_rel_rmse'] * 100:.1f}% of the average price, against "
             f"{PA_TEST['ann_rel_rmse'] * 100:.1f}% for the ANN, and it broke the pricing equation "
             f"{PA_TEST['ann_pde_residual_rms'] / PA_TEST['pinn_pde_residual_rms']:.0f} times less. Where it had no data, the ANN "
             f"guessed: on the slice above it priced {_NEG('ann')} of {_NPTS:,} points below zero by more than 0.2% of the "
             f"strike, which no option can be worth. The PINN priced {'none' if _NEG('pinn') == 0 else _NEG('pinn')}.")
PA_NOTE = ("A demonstration run for this site (website/tools/pinn_vs_ann.py, about 3 minutes on a laptop): same architecture, "
           "same seed, same data, same training steps for both networks. The research PINNs are larger and trained far longer.")
PA_NUMS = [(f"{PA_TEST['pinn_rel_rmse'] * 100:.1f}%", "PINN error, share of the average price"),
           (f"{PA_TEST['ann_rel_rmse'] * 100:.1f}%", "ANN error on the same points"),
           (f"{PA_TEST['ann_pde_residual_rms'] / PA_TEST['pinn_pde_residual_rms']:.0f}×", "smaller pricing-equation error for the PINN")]

# ------------------------------------------------------------------ results (stats) page
RESULTS_HEAD = "Every result, and the data behind it"
RESULTS_LEDE = ("All the project's numbers in one place: what we measured, on which data, and whether it's good news. "
                "Negative results are kept, because they are part of the answer.")
DATA_SETS = [  # (name, size, what it is)
    ("Market display", f"{N_DAYS} trading days", f"NSE closing prices, {FIRST_DAY} to {LAST_DAY}, for NIFTY 50, NIFTY BANK and the stocks on the Market page."),
    ("NIFTY option chain", f"{len(D['chain'])} strikes", f"NIFTY options expiring {EXPIRY}, closing prices on {LAST_DAY}, with traded volume, open interest and trades above zero."),
    ("Real option surfaces", "12,480 surfaces", "210 NSE stocks × 60 trading days (12,600 attempted, 120 rejected by the data checks). Each surface targets 20 quotes; a typical one has 17."),
    ("Ambiguity study", "2,400 surfaces", "The 40 most traded of those stocks over the same 60 days, each surface fitted from 16 starting points."),
    ("Simulated surfaces", f"{CB['surfaces_calibrated']} surfaces", "Made by our own pricer from known settings, so the right answer is known."),
    ("ANN test set", f"{NET['test_samples']:,} surfaces", "Simulated surfaces the ANN never saw while learning."),
    ("Held-out dates", "8 dates", "Later trading dates the ANN never saw, used to test it on real quotes."),
    ("Backtest", f"{BT_PAIRS:,} stock-days", "Every stock and pair of consecutive trading days: settings from one day used to price the next."),
    ("PINN training", "100,000 + 18,000", "Exact Double Heston prices to learn from, plus points where the pricing equation itself is enforced."),
    ("NIFTY, high volatility", "10 days, 1,750 quotes", "The 10 NIFTY dates of 2026 with the highest recent realised volatility, chosen by a rule fixed before any fit."),
]
RESULTS = [  # (result, value, what it measures, verdict: good | mixed | bad)
    ("Double Heston against one flat volatility", f"{FLAT_BETTER * 100:.0f}% less error", "Median price error of the best fit on 2,400 real surfaces; it was ahead on every one.", "good"),
    ("Fitting simulated prices", "9.16 × 10⁻⁸", "Median price error of a classical optimizer on 60 simulated surfaces.", "good"),
    ("Reading the settings back", f"{CB['mean_median_skill']:.2f}", "Recovery skill on the same surfaces; 1.00 is always guessing the typical value, lower is better.", "bad"),
    ("Several equally good fits", f"{SHARE * 100:.0f}%", "Share of 2,400 real surfaces where more than one set of settings priced equally well (within 10% of the best price error).", "bad"),
    ("How far apart they sat", f"{RATIO:.1f}×", f"Median distance between equally good fits ({AMB['median_dispersion']:.2f}) against two random settings ({RAND:.2f}).", "bad"),
    ("Today's level", f"{[p for p in D['per_param'] if p['name'] == 'v0_s'][0]['fits']:.2f}", "Distance between equally good fits for the slow factor's level, against about 0.95 at random: pinned down.", "good"),
    ("Speeds back to normal", f"{[p for p in D['per_param'] if p['name'] == 'kappa_s'][0]['fits']:.2f}", "Distance for the slow factor's speed, against about 0.90 at random: not pinned down at all.", "bad"),
    ("ANN, reading the settings", f"{NET['mean_skill']:.2f}", f"RMSE-based recovery skill on {NET['test_samples']:,} simulated surfaces, against {CB['mean_skill']:.2f} for the optimizer.", "mixed"),
    ("ANN on dates it never saw", f"{G8['median_network_relative'] * 100:.1f}%", f"Median repricing error on 8 later dates, against {G8['median_best_fit_relative'] * 100:.1f}% for the best possible fit.", "bad"),
    ("ANN settings against Black–Scholes", BEAT_BS_NUM, f"Stock-days where Double Heston with the ANN's settings priced better than a same-day Black–Scholes fit ({BT_SAME_DAY_N:,} of {BT_PAIRS:,}).", "bad"),
    ("Next day, against Black–Scholes", f"{BT_NEXT_DAY * 100:.1f}%", "Stock-days where yesterday's settings beat yesterday's Black–Scholes volatility on today's quotes.", "mixed"),
    ("PINN fidelity", "1.1 × 10⁻⁵", "Price error of the Double Heston PINN against the exact pricer on 8,192 points it never saw (0.1 volatility points).", "good"),
    ("PINN, controlled test", "40 of 40", "Surfaces where the PINN beat a refitted one-factor Heston, which beat Black–Scholes.", "good"),
    ("PINN calibrator on NIFTY", f"{PINN_NIFTY['ft_3']:.2f} pts", f"Median error in volatility points on 1,750 held-out quotes, against {PINN_NIFTY['bs']:.2f} for Black–Scholes; best on {PINN_NIFTY_BEST} of 10 days.", "good"),
    ("PINN against ANN (demonstration)", f"{PA_TEST['pinn_rel_rmse'] * 100:.1f}% vs {PA_TEST['ann_rel_rmse'] * 100:.1f}%", "Price error of two identical networks trained on the same data, with and without the pricing equation.", "good"),
]
TERMS = [  # (term, plain meaning)
    ("Option surface", "All of one stock's option prices on one day, across strikes and expiries."),
    ("Setting (parameter)", "One of Double Heston's ten numbers: for each factor, today's level, long-run level, speed back to normal, volatility of volatility and link to price moves."),
    ("Equally good fit", "A set of settings whose price error is within 10% of the best one found for that surface."),
    ("Distance between fits", "How far apart two sets of settings are, measured in spreads of the settings seen in the training data, so every setting counts equally."),
    ("Recovery skill", "Error in the settings divided by the error from always guessing the typical value. 1.00 is no better than guessing; lower is better."),
    ("Volatility point", "One percentage point of implied volatility, for example 15% against 16%."),
    ("Stock-day", "One stock on one trading day."),
    ("Held out", "Data the model never saw while it was being built, kept back to test it fairly."),
]

# ------------------------------------------------------------------ titles and how-to-read lines for every chart
CHART_NOTES = {
    "smileBend": ("Implied volatility by strike, 30 days to expiry",
                  "Strike on the left axis is a percentage of today's price; height is implied volatility. The dashed line is Black–Scholes' one volatility; the solid line is Double Heston at its starting settings."),
    "marketSmile": ("Market against model, by strike",
                    "Rings are NSE closing prices turned into implied volatility; the line is Double Heston at your settings. The dotted line marks today's NIFTY level."),
    "candles": ("Daily candlesticks with volume",
                "Each candle is one day: the body runs from open to close, the thin line from low to high. Green closed higher, red lower. Volume is shaded underneath; the tag on the right is the last close."),
    "indexLine": ("Closing level by day", "One point per trading day; the shaded area sits under the line. Hover for the date and level."),
    "hist": ("How far apart equally good fits landed, per surface",
             "Each bar counts surfaces by the distance between their equally good fits. The dashed line is the typical distance between two random settings; the solid line is the median for equally good fits."),
    "paramBars": ("Distance between equally good fits, setting by setting",
                  "Bars show how far apart equally good fits landed for each setting; the tick shows two random settings. A bar shorter than its tick means the prices pin that setting down."),
    "stockPanel": ("One stock over 60 trading days",
                   "Top: price error each day for the best Double Heston fit (solid) and one flat volatility (dashed). Bottom: how far apart that day's equally good fits landed; the dashed line is two random settings."),
    "skew": ("Skew by time to expiry",
             "How many volatility points dearer protection against a fall is than a bet on a rise, at each expiry. The time axis is stretched so short expiries are readable."),
    "decay": ("How fast each factor forgets a shock",
              "Share of a volatility shock left after each period. Dots mark the half-life: where half the shock is gone."),
    "fan": ("Simulated price paths for one year",
            "Thin lines are individual simulated paths from 100; shading covers the middle 50% and 90% of 400 paths; the bold line is the median."),
    "surface": ("Implied volatility for every strike and expiry",
                "Rows are time to expiry, columns are strike as a percentage of today's price. Darker cells mean higher implied volatility; ≈ 0 marks options worth almost nothing."),
    "pairPool": ("Bharti Airtel, 39-day options: two fits on top of each other",
                 "Rings are the market's prices as implied volatility; the filled curve is fit A and the dotted line fit B. They lie almost exactly on each other."),
    "pairMagnets": ("The ten settings of each fit",
                    "One spike per setting; height is the setting's size on its own scale. Compare the rows: same prices, very different settings."),
    "pairPart": ("At-the-money volatility by time to expiry, both fits",
                 "The shaded band covers the expiries that traded that day. Rings are the market's at-the-money prices. Past the band, the fits disagree."),
    "pairSix": ("Each setting of all six equally good fits",
                "Each spike is one fit's value on that setting's scale. Spikes bunched together mean the prices pin the setting; spread out means they don't."),
    "factorTrace": ("The two variance factors, simulated live",
                    "The model's own variance equation at its starting settings, run forward as you watch, shown as volatility in percent. The fast factor jitters and snaps back; the slow one drifts."),
    "pinnAnn": ("Option price surface at today's volatility: ANN, PINN and the exact pricer",
                "Height is the call price as a share of the strike; across is the share price as a share of the strike, and depth is time to expiry. Coloured surfaces are each network; the grey mesh is the exact pricer. Drag to turn."),
    "journey": ("A random walk, drawn as the timeline unfolds",
                "A simulated Brownian path: each step is a random kick, the motion Einstein explained and finance borrowed."),
}
