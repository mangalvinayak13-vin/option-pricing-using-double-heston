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
              "During market hours the site shows live prices from Upstox in the same places.")
STATUS = f"Market closed. Last close {LAST_DAY}, 15:30 IST"
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
PROOF1_NET = (f"A neural network trained to read the settings from prices scores {NET['mean_skill']:.2f} on the RMSE-based "
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
HELDOUT = (f"On 8 later dates the model never saw, a trained network repriced options with a median error of "
           f"{G8['median_network_relative'] * 100:.1f}%, against {G8['median_best_fit_relative'] * 100:.1f}% for the best "
           f"possible fit: a gap of {G8['median_gap_pp']:.1f} points.")
BACKTEST = ("Across 210 stocks and 60 days, prices from the network's settings lost to a single flat volatility on "
            "every one of the 210 stocks.")
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
METHOD = [
    "Prices come from the characteristic-function formula and are checked against Monte Carlo simulation.",
    f"Research data: official NSE end-of-day files, 210 stocks, 60 trading days, 12,480 option surfaces. "
    "Live prices on the site come from Upstox.",
    "Every real-market result was re-run after three pipeline bugs were found and fixed, and checked against a flat "
    "volatility, which a true best fit can never lose to.",
]
LIMITS = [
    "No jumps: the largest one-day moves are still underestimated.",
    "Dividends are supported but set to zero; one interest rate for every maturity.",
    "Prices are frictionless. Real trading crosses a bid–ask spread.",
    "End-of-day research data has closing prices only, no bid–ask quotes.",
    "Only 11 to 19 of the 20 target option slots are quoted on a typical day.",
]
ALSO = ("Whether EWMA or GARCH forecasts of next month's volatility beat simply assuming it looks like "
        "last month, tested walk-forward over 60 stocks and ten years.")

# ------------------------------------------------------------------ team -----------------
TEAM_HEAD = "The team"
TEAM_INTRO = "Built for [Event] at [College]. Replace each placeholder with the real name and what that person built."
TEAM = [("[Name]", "[Role: e.g. model and pricer]"), ("[Name]", "[Role: e.g. data pipeline]"),
        ("[Name]", "[Role: e.g. website and design]"), ("[Name]", "[Role: e.g. research and report]")]
SUPERVISOR = ("[Supervisor name]", "[Department], [College]")
THANKS = ["NSE, for the public end-of-day files the research uses.", "Upstox, for the market-data API behind the live prices.",
          "The authors of NumPy, SciPy and pandas."]

# ------------------------------------------------------------------ references -----------
REFS = [
    ("Models", [
        ("Black, F. and Scholes, M. (1973)", "The pricing of options and corporate liabilities.", "Journal of Political Economy 81(3)."),
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
        ("Bachelier, L. (1900)", "Théorie de la spéculation.", "Annales scientifiques de l'École normale supérieure 17."),
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
