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
DH_BEAT_ALL = 1 - D["dh_worse_than_flat_share"]  # 1.0: Double Heston beat flat volatility on every one of 2,400 surfaces
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
CTA = {"model": "Price an option", "finding": "See the results", "market": "Open the market"}

# ------------------------------------------------------------------ market ---------------
MARKET_TITLE = "Market"
MARKET_SUB = (f"Daily history starts {FIRST_DAY}: NSE's official closes to {LAST_DAY}, then Upstox daily candles "
              "up to today. The prices, today's candle and the day's figures are live from Upstox while the "
              "market's open.")
STATUS = f"Prices as of the NSE close, {LAST_DAY}, 15:30 IST"
LIVE_LOADING = "Checking for live prices…"
LIVE_OPEN = "Live, updated {time} IST"
LIVE_CLOSED = "Market closed — last traded price shown"
LIVE_FALLBACK = "Live prices unavailable right now — the numbers above are NSE's last close."
UNIVERSE = "NIFTY 50, NIFTY BANK and the 40 most traded F&O stocks: every stock we show an implied volatility for."

# ------------------------------------------------------------------ model ----------------
CONTRACT = f"NIFTY {inr(K['strike'], 0)} call"
CONTRACT_SUB = f"Expires {EXPIRY}, {K['dte']} days"
MODEL_EXPLAIN = (f"The starting settings assume 20% volatility. On {LAST_DAY} the market was pricing about "
                 f"{K['market_iv']:.1f}%, so the model charges more. Lower today's level (v₀) and the gap closes. "
                 "There's no fit button: the Results page explains why a computer can't pick all ten settings for you.")
GAP = K["dh"] - K["market"]
MC_LINE = f"Monte Carlo check, 20,000 paths: ₹{inr(K['mc'])} ± {K['mc_se']:.2f}"
MODEL_SOURCE = (f"Option prices: NSE closing prices, {LAST_DAY}. Forward from NIFTY October futures "
                f"({inr(K['forward'])}). Rate: RBI 91-day T-bill, 15 Jul observation carried forward, as in the research.")
SLIDERS = [  # (factor, symbol, name, value, lo, hi)
    ("slow", "v₀", "Today's variance", 0.02, 0.0005, 1.0), ("slow", "κ", "Speed back to normal", 0.5, 0.1, 10.0),
    ("slow", "θ", "Long-run variance", 0.02, 0.0005, 1.0), ("slow", "ξ", "Volatility of volatility", 0.3, 0.05, 2.0),
    ("slow", "ρ", "Price–volatility link", -0.7, -0.99, 0.99),
    ("fast", "v₀", "Today's variance", 0.02, 0.0005, 1.0), ("fast", "κ", "Speed back to normal", 5.0, 0.1, 10.0),
    ("fast", "θ", "Long-run variance", 0.02, 0.0005, 1.0), ("fast", "ξ", "Volatility of volatility", 0.5, 0.05, 2.0),
    ("fast", "ρ", "Price–volatility link", -0.7, -0.99, 0.99),
]
FELLER = {"slow": "Feller condition fails: 2κθ = 0.02 is below ξ² = 0.09", "fast": "Feller condition fails: 2κθ = 0.20 is below ξ² = 0.25"}
FELLER_NOTE = ("Both factors can touch zero at these settings. The simulator uses full truncation, so prices stay valid.")
GREEKS = [("Delta", f"{K['delta']:.3f}", "per ₹1 move in NIFTY"), ("Gamma", f"{K['gamma']:.5f}", "change in delta per ₹1"),
          ("Vega", f"{K['vega']:.1f}", "₹ per volatility point"), ("Theta", f"{K['theta']:.2f}", "₹ per calendar day"),
          ("Rho", f"{K['rho']:.1f}", "₹ per rate point")]
CHAIN = [r for r in D["chain"] if abs(r["strike"] - K["strike"]) <= 250]

# ------------------------------------------------------------------ maths ----------------
MATHS_INTRO = ("An option's price depends on how jumpy the stock will be before it expires. Black–Scholes assumes one "
               "fixed jumpiness. Double Heston (Christoffersen, Heston and Jacobs, 2009) lets it move, and splits it "
               "into two parts that move on their own: a fast one for sudden scares and a slow one for long moods. "
               "Below is the whole model, one formula at a time.")
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
FIND_HEAD = "It beat flat volatility on every surface we tested. Knowing why takes more than a perfect fit."
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
BACKTEST = (f"A same-day Black–Scholes fit is a hard bar to clear: it gets refit fresh to that day's own prices, while "
            f"Double Heston here is using settings our ANN read earlier. Even so, with the settings our ANN reads from "
            f"each day's own quotes, Double Heston priced that day's options better than that fresh same-day "
            f"Black–Scholes fit on {BT_SAME_DAY * 100:.1f}% of {BT_PAIRS:,} stock-days ({BT_SAME_DAY_N:,} of them). The fairer, "
            f"same-conditions comparison carries both forward one day unrefit: there, Double Heston's carried-forward "
            f"settings beat Black–Scholes's on {BT_NEXT_DAY * 100:.1f}%.")
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
    "Research data: official NSE end-of-day files. Every dataset, its size and what it was used for is listed on the Results page.",
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
    ("results", "results.html", "Results", "what we found, every number"),
    ("about", "about.html", "About", "video, method, limits"),
    ("team", "team.html", "Team", "who built it"),
    ("references", "references.html", "References", "papers and data"),
]
# pages that exist but stay out of the navs, dock and page links, with the page they sit under:
# Market is reached from the button at the top right of Price an option (and the ticker)
NAV_PARENT = {"market": "model"}
MARKET_BUTTON = "Market prices"
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
FAN_NOTE = (f"Sixty of 400 simulated one-year paths, all starting at 100, with the middle 50% and 90% of the 400 shaded. "
            f"The same simulator checks the pricer: 20,000 paths price the NIFTY {inr(K['strike'], 0)} call at ₹{inr(K['mc'])} "
            f"± {K['mc_se']:.2f}, against ₹{inr(K['dh'])} from the formula.")
FACTORS_HEAD = "Two volatilities, one fast and one slow."
FACTORS = (f"Each factor gets knocked about and drifts back to its long-run level. The fast one (κ 5.0) loses half "
           f"of any shock in {FAST_HL}; the slow one (κ 0.5) takes {SLOW_HL}. Same kind of process, different clocks.")


# ------------------------------------------------------------------ home: from Einstein's random walk to Wall Street
JOURNEY_HEAD = "Twelve steps from a jiggling grain to option prices"
HERO_KEYS = ("from", "to")  # Amber's readout labels for those two parts
A_NO = "Reading its settings? No."
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
PA_WHY = ("Why a PINN at all: reading a stock's ten settings off its option prices normally means a classical optimizer "
          "searching from several starting points, which takes seconds to minutes per surface and, as the Results page "
          "shows, can still land on settings that break the model's own rules. A physics-informed network is built "
          "differently — trained to obey Double Heston's pricing equation itself, not just copy examples, with its "
          "output wired so it cannot propose a setting that violates the model's constraints. Trained once, it then "
          "reads a full day's settings in a fraction of a second, not minutes.")
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
PA_NOTE = ("A demonstration run for this site (about 3 minutes on a laptop): same architecture, "
           "same seed, same data, same training steps for both networks. The research PINNs are larger and trained far longer.")
_PS = json.loads((_DATA_DIR / "pinn_vs_ann_steps.json").read_text())
PA_STEPS = [c for c in _PS["checkpoints"] if c > 0]  # replay frames; step 0 is the same random start for both, far off the scale
_imp = {n: {f["step"]: f["impossible"] for f in _PS[n]} for n in ("ann", "pinn")}
_ann_low = min(PA_STEPS, key=lambda c: _imp["ann"][c])
PA_REPLAY = (f"Replay the training and the difference grows. The ANN's impossible prices fell to {_imp['ann'][_ann_low]} by step "
             f"{_ann_low:,}, then climbed back to {_imp['ann'][PA_STEPS[-1]]} as it fitted its 48 prices ever more tightly. "
             f"The PINN's fell to {_imp['pinn'][PA_STEPS[-1]] or 'zero'}: the equation kept it honest where it had no data.")
PA_NUMS = [(f"{PA_TEST['pinn_rel_rmse'] * 100:.1f}%", "PINN error, share of the average price"),
           (f"{PA_TEST['ann_rel_rmse'] * 100:.1f}%", "ANN error on the same points"),
           (f"{PA_TEST['ann_pde_residual_rms'] / PA_TEST['pinn_pde_residual_rms']:.0f}×", "smaller pricing-equation error for the PINN")]

# ------------------------------------------------------------------ Home, simpler version: the physics behind it
# Home is only: the line in quotes, where it starts (Einstein, 1905, with context), the project's two aims, and the
# four models from Brownian motion to Double Heston. Written for readers who have just finished class 12.
# The line is the site's own, not a quotation: Einstein's name sits under it as where the story starts.
HERO_TITLE = ("“From a speck of pollen", "to Wall Street”")
HERO_BY = "Where it starts: Albert Einstein, 1905"
HERO_LEAD = ("In 1827 the botanist Robert Brown saw tiny specks from pollen jiggling in still water, and nobody could "
             "say why. In 1905 Albert Einstein explained it: water molecules, far too small to see, hit each speck from "
             "every side at random. That random jiggle, called Brownian motion, is where every model on this page starts.")
EINSTEIN_HEAD = "What Einstein worked out"
EQ_EINSTEIN = "⟨x²⟩ = 2Dt"
EINSTEIN = ("A speck kicked at random doesn't travel in a straight line. Einstein showed that, on average, the square of "
            "the distance it wanders grows in step with time. So the typical distance grows with the square root of "
            "time: wait four times as long and it goes only twice as far.")
EINSTEIN_SYMS = [("⟨x²⟩", "Average of the distance squared"), ("D", "How easily it spreads: set by the water's temperature, its stickiness and the speck's size"),
                 ("t", "Time")]
EINSTEIN_NEXT = ("Five years before Einstein, Louis Bachelier in Paris had already used the same random walk for share "
                 "prices. In 1923 Norbert Wiener wrote one random kick as exact maths, called dW. Every equation below is "
                 "built from that dW.")
AIMS_HEAD = "What this project sets out to show"
AIMS = [
    ("Double Heston, grown step by step from Brownian motion",
     "Start with Einstein's random kick. Use it for a share price, and you get geometric Brownian motion. Price an option "
     "from it, and you get Black–Scholes. Let the price's jumpiness take random kicks of its own, and you get Heston. Give "
     "that jumpiness two speeds, one fast and one slow, and you get Double Heston. The four steps are below."),
    ("A PINN to read the model's ten settings",
     "Double Heston has ten settings. Finding them from a day's prices by trial and error takes seconds to minutes, and "
     "can still land on settings that break the model's own rules. A PINN (physics-informed neural network) is a neural "
     "network that must also obey the model's pricing equation, a diffusion equation from the same family as Einstein's. "
     f"On real NIFTY options it was off by {PINN_NIFTY['ft_3']:.2f} volatility points, against {PINN_NIFTY['bs']:.2f} for "
     f"Black–Scholes, and took {PINN_NIFTY_SECONDS[0]:.1f} seconds instead of {PINN_NIFTY_SECONDS[1]:.0f}. In a "
     f"side-by-side test, a plain network priced {_NEG('ann')} of {_NPTS:,} points below zero, which no option can be "
     f"worth. The PINN priced {'none' if _NEG('pinn') == 0 else _NEG('pinn')}."),
]
MODELS_HEAD = "Four models, one step at a time"
MODELS_LEDE = ("Each model keeps everything from the one before and lets one more thing move at random. Hover over the "
               "triangle on any card for an everyday picture.")
MODELS = [  # (key, year, who, name, settings, plain equation, in words, what it fixed, what still breaks)
    ("gbm", "1965", "Paul Samuelson, after Louis Bachelier (1900)", "Geometric Brownian motion", "2 settings: μ and σ",
     "dS = μ S dt + σ S dW",
     "In each tiny moment, the price grows by a steady percentage (μ) plus a random kick (σ dW). The kick is Einstein's "
     "Brownian kick, but measured in percent of the price, not in rupees.",
     "Bachelier's kicks were in rupees, so his prices could fall below zero. Kicks in percent never take a price below zero.",
     "It describes the share. It doesn't yet say what an option on the share is worth."),
    ("bs", "1973", "Fischer Black, Myron Scholes and Robert Merton", "Black–Scholes", "1 setting: σ",
     "∂V/∂t + ½σ²S² ∂²V/∂S² + rS ∂V/∂S − rV = 0",
     "Take the same share. Mix the option with just the right amount of share and the random kicks cancel out. A mix "
     "with no risk must earn the same as a bank deposit, at rate r. That one idea gives this equation for the option's "
     "price V, and μ drops out. Change the variables and it turns into the heat equation, the same equation that "
     "describes Einstein's spreading specks.",
     "A fair price for an option, from one formula.",
     "It keeps the jumpiness σ fixed for ever, so every strike gets the same volatility: a flat line. After the 1987 "
     "crash, real prices bent instead. Insurance against a fall started costing more."),
    ("heston", "1993", "Steven Heston", "Heston", "5 settings: v₀, θ, κ, ξ, ρ",
     "dS = r S dt + √v S dW,   dv = κ (θ − v) dt + ξ √v dZ,   corr(dW, dZ) = ρ",
     "Now the jumpiness itself (v, the variance) takes random kicks of its own, dZ. A spring pulls it back toward its "
     "normal level θ at speed κ, and ξ sets how hard it is shaken. ρ links the two kicks: when it is negative, falls in "
     "price come with rising jumpiness.",
     "The bend. Insurance against a fall now costs more, as it does in real markets.",
     "It has one clock. A scare that fades in weeks and a mood that lasts a year can't share one speed, so options "
     "expiring next week and next year don't fit together."),
    ("dh", "2009", "Peter Christoffersen, Steven Heston and Kris Jacobs", "Double Heston", "10 settings: five for each part",
     f"{EQ_PRICE},   {EQ_VAR}",
     f"Two jumpiness levels, each on its own spring: a fast one, which loses half of any shock in {FAST_HL}, and a slow "
     f"one, which takes {SLOW_HL}. Four random kicks drive it: two on the price and one on each jumpiness.",
     f"Short and long expiries together. On all 2,400 real NSE price lists we tested, it beat one fixed volatility, with "
     f"{FLAT_BETTER * 100:.0f}% less error on a typical one.",
     f"On {SHARE * 100:.0f}% of those price lists, several different sets of ten settings fitted equally well, so the "
     "prices alone can't tell you which is right. That is why we built a PINN to read them."),
]

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
                "Each candle is one day: the body runs from open to close, the thin line from low to high. Green closed higher, red lower. Volume is shaded underneath (for an index, the shares traded across its stocks); the tag on the right is the last close."),
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
                "Height is the call price as a share of the strike; across is the share price as a share of the strike, and depth is time to expiry. The solid surface is the network's price and the grey grid is the exact Double Heston price, so wherever they part, the network is wrong. Error shows only that gap, on the same scale for both. The slider replays training. Drag to turn."),
    "journey": ("A random walk, drawn as the timeline unfolds",
                "A simulated Brownian path: each step is a random kick, the motion Einstein explained and finance borrowed."),
}


# ------------------------------------------------------------------ consolidation: one Results page, a short summary on Home
RESULTS_PAGE_HEAD = FIND_HEAD
RESULTS_PAGE_LEDE = ("Everything the project found, in one place: the win in numbers, the evidence behind it, what our "
                     "two kinds of network achieved, then every result in a table with the data it came from — including "
                     "the results that didn't work, because that's how you know the ones that did are real.")
KEY_NUMS = [  # the answer in numbers: the win first, then the finding that explains why it's worth trusting
    (f"{DH_BEAT_ALL * 100:.0f}%", f"of 2,400 real surfaces: Double Heston beat one flat volatility ({FLAT_BETTER * 100:.0f}% less error, median)"),
    (f"{PINN_NIFTY['ft_3']:.2f} vs {PINN_NIFTY['bs']:.2f}", "PINN against Black–Scholes on real NIFTY options, volatility points"),
    (f"{SHARE * 100:.0f}%", "of those surfaces had several equally good fits — a finding, not a flaw: it's why every result here was checked this hard"),
    (f"{RATIO:.1f}×", "further apart than two random sets of settings, when that happens"),
]
KEY_HEAD = "What we found, in four numbers"
KEY_LEDE = ("Double Heston fits real option prices better than one flat volatility, every time we checked — but the "
            "prices alone can't tell you which of its ten settings did it. The Results page has the evidence behind "
            "every number.")


# ------------------------------------------------------------------ How it works: the model, one formula at a time
FORMULAS_HEAD = "The model, one formula at a time"
FORMULAS_LEDE = "Each card gives the formula, what its symbols mean and what it does. Open “Explain simply” for an everyday picture of it."
FORMULAS = [  # (key, title, plain formula for screen readers, what it does, [(symbol, meaning)])
    ("price", "The price moves with two variances", EQ_PRICE,
     "Over a tiny moment of time, the share price drifts at the interest rate minus the dividend yield, and gets two "
     "random kicks. How big each kick is depends on one of the two variances.",
     [("S", "share price"), ("r", "interest rate"), ("q", "dividend yield"), ("v₁, v₂", "the two variances, slow and fast"),
      ("dW₁, dW₂", "two independent random shocks"), ("dt", "a tiny step of time")]),
    ("variance", "Each variance drifts back to normal", EQ_VAR,
     "Each variance is pulled back toward its long-run level θ at speed κ, and shaken by random shocks of size ξ. "
     "Its shocks move with the price's shocks at correlation ρ. A negative ρ means falls come with rising volatility, "
     "which is what tilts the smile.",
     [("vᵢ", "today's variance of factor i"), ("θᵢ", "the long-run level it returns to"), ("κᵢ", "how fast it returns"),
      ("ξᵢ", "how hard it gets shaken"), ("dZᵢ", "its own random shock"), ("ρᵢ", "the link between price and variance shocks"),
      ("i", "1 for the slow factor, 2 for the fast one")]),
    ("cf", "Independent factors multiply", EQ_CF,
     "The characteristic function φ is a compact fingerprint of where the price could end up. Because the two factors "
     "are independent, the model's fingerprint is just the product of each factor's own, so pricing stays fast.",
     [("φ(u)", "the model's fingerprint, read at frequency u"), ("φ₁, φ₂", "the slow and fast factors' own fingerprints")]),
    ("call", "One integral gives the price", EQ_CALL,
     "A call is worth what you expect to receive above the strike, minus what you expect to pay, brought back to "
     "today's money. P₂ is the chance, under the pricing measure, that the option ends in the money; P₁ is the same "
     "chance counted in shares. Both come out of the fingerprint through one integral (Gil-Pelaez). The code uses the "
     "“little trap” form (Albrecher et al., 2007), which avoids a branch-cut error in the 1993 formula at long expiries.",
     [("C", "call price"), ("F", "forward price of the share"), ("K", "strike"), ("T", "time to expiry, in years"),
      ("e^(−rT)", "discount back to today"), ("P₁, P₂", "the two probabilities"), ("Re", "real part of a complex number")]),
    ("mc", "Check by simulation", "C ≈ e^(−rT) · (1/N) Σₙ max(S_T⁽ⁿ⁾ − K, 0)",
     f"Monte Carlo prices the same option the slow way: simulate 20,000 possible paths of the price and both variances, "
     f"average what the call pays at expiry, and discount. The paths use full-truncation Euler steps and antithetic "
     f"pairs. For the NIFTY {inr(K['strike'], 0)} call it gives ₹{inr(K['mc'])} ± {K['mc_se']:.2f}, against "
     f"₹{inr(K['dh'])} from the formula: inside the simulation's own margin of error.",
     [("N", "number of simulated paths, 20,000"), ("S_T⁽ⁿ⁾", "the share price at expiry on path n"),
      ("max(S − K, 0)", "what a call pays at expiry")]),
    ("feller", "When a factor can't touch zero", EQ_FELLER,
     "If 2κθ is bigger than ξ², that factor's variance never reaches zero. Real markets often break this. When a "
     "simulated variance would go below zero, the simulator holds it at zero for that step (full truncation), so prices "
     "stay valid.",
     [("κᵢ, θᵢ, ξᵢ", "the speed, long-run level and shake of factor i")]),
]
# each symbol's meaning starts with a capital, like any label
FORMULAS = [(k, t, plain, what, [(sym, m[:1].upper() + m[1:]) for sym, m in syms]) for k, t, plain, what, syms in FORMULAS]
SETTINGS_HEAD = "The ten settings"
SETTINGS_LEDE = ("Each factor has the same five settings, so the model has ten. Here is what each one controls and what "
                 "raising it does. The starting values are the ones Price an option opens with.")
SETTINGS = [  # (symbol, name, what it controls, what raising it does, slow start, fast start)
    ("v₀", "Today's variance", "How jumpy the stock is right now. Variance is volatility squared: 0.02 is about 14% a year.",
     "Options cost more now, short-dated ones most.", "0.02", "0.02"),
    ("θ", "Long-run variance", "The level the jumpiness settles back to over time.",
     "Long-dated options cost more.", "0.02", "0.02"),
    ("κ", "Speed back to normal", f"How fast jumpiness returns to its long-run level after a shock. Half of a shock is gone "
     f"after ln 2 ÷ κ years: {SLOW_HL} for the slow factor, {FAST_HL} for the fast one.",
     "Shocks fade faster, so the factor matters less for long-dated options.", "0.5", "5.0"),
    ("ξ", "Volatility of volatility", "How much the jumpiness itself jumps around.",
     "The smile curves more: options far from today's price cost more.", "0.3", "0.5"),
    ("ρ", "Price–volatility link", "Whether jumpiness rises when the price falls (negative) or when it rises (positive), from −1 to 1.",
     "Toward −1: protection against falls gets dearer than bets on rises, so the smile tilts more.", "−0.7", "−0.7"),
]

# ------------------------------------------------------------------ "Explain simply": (everyday picture, what it means here)
EXPLAIN = {
    # Home: Einstein and the four models
    "einstein": ("A crowd leaving a cricket stadium. Each person turns left or right at random. After one minute the crowd "
                 "has spread a little; after four minutes, only twice as far, not four times.",
                 "Random steps partly cancel out, so spreading grows with the square root of time."),
    "m-gbm": ("A speck in water whose kicks grow with its size: a ₹2,000 share gets bigger rupee kicks than a ₹20 one, but "
              "the same kicks in percent.", "That is why the price can never fall below zero."),
    "m-bs": ("Two friends bet in opposite directions on the same match. Whatever happens, together they neither win nor lose.",
             "Mix the option and the share the right way and the risk cancels, so the mix must earn what a bank pays."),
    "m-heston": ("The weather has moods. A calm week can turn stormy, and storms die down again.",
                 "In Heston the jumpiness changes too, and is always pulled back toward normal, like a ball on a spring."),
    "m-dh": ("A cup of chai and a big kettle, both just boiled. The cup cools in minutes; the kettle stays warm for hours.",
             f"The fast part forgets a shock in weeks (half gone in {FAST_HL}); the slow part takes {SLOW_HL}."),
    # the formulas
    "f-price": ("Think of a boat on a river. The current carries it steadily downstream: that's the drift, r − q. Two kinds "
                "of waves rock it at once, short choppy ones and long swells. How rough each kind is right now is v₁ and v₂.",
                "So the price wanders at random, and how wildly depends on two separate, changing levels of jumpiness."),
    "f-variance": ("Picture a ball on a spring. θ is where the spring rests, κ is how stiff it is, and ξ is how hard someone "
                   "keeps shaking it. ρ says which way the shaking leans.",
                   "In stock markets fear rises when prices fall, so ρ is usually negative, and that is what makes "
                   "protection against a fall cost more."),
    "f-cf": ("Two independent dice. To find the chance of each total you could list all 36 combinations, or combine each "
             "die's fingerprint with one multiplication. Independence is what makes the shortcut work.",
             "That is why two factors cost little more to price than one."),
    "f-call": ("Like a receipt for a bet. One line is what you expect to collect if the share ends above the strike (F·P₁). "
               "The next is the strike you expect to pay (K·P₂). The difference, brought back to today's money, is the fair price.",
               "The integral is only the step that turns the model's fingerprint into those two chances."),
    "f-mc": ("Instead of working out a die's average on paper, roll it 20,000 times and average the rolls.",
             "If the formula and the simulation agree, the formula is coded right. They agree to within the simulation's "
             "own margin of error."),
    "f-feller": ("A ball on a spring above the floor. If the spring pulls back hard enough (2κθ) compared with how hard it's "
                 "shaken (ξ²), the ball never touches the floor.",
                 "Here the floor is zero variance. At the starting settings both factors break the condition, so the "
                 "simulator stops the variance at zero instead of letting it go negative."),
    # the settings, as weather
    "s-v₀": ("Today's weather.", "It sets the price of options that expire soon, before the weather has time to change."),
    "s-θ": ("The climate: what the weather averages out to.", "It matters most for options with a long time to run."),
    "s-κ": ("How quickly the sky clears after a storm.",
            "Option prices barely depend on it, which is why equally good fits disagree about it most."),
    "s-ξ": ("How changeable the weather is: calm and predictable, or sun and hail in the same hour.",
            "More of it makes extreme moves likelier, so options far from today's price get dearer."),
    "s-ρ": ("Whether storms tend to arrive when prices drop.", "In stock markets they usually do, so ρ is usually negative."),
    # How it works charts
    "bend": ("Black–Scholes draws the market with a ruler: one straight volatility for every strike. Double Heston uses a "
             "flexible curve.", "Real option prices bend, so the curve fits and the ruler can't."),
    "decay": ("Two cups of coffee cooling: a small cup is cold in minutes, a big pot stays warm for hours. Same law, "
              "different speeds.", f"Half of a shock to the fast factor is gone in {FAST_HL}; in the slow factor it takes {SLOW_HL}."),
    "factors": ("Two dogs walked side by side, one on a short leash and one on a long one. The first darts about but stays "
                "close; the second wanders slowly and far.", "The fast factor jitters and snaps back; the slow one drifts."),
    "skew": ("A fresh scare matters a lot for next week and much less for next year, because it has time to fade.",
             "So the extra cost of protection against a fall shrinks as expiry gets further away."),
    "fan": ("Like a weather forecast cone: tomorrow is fairly certain, next month much less.",
            "The shaded bands show how far simulated prices spread over a year. Averaging what an option pays across "
            "paths like these gives the Monte Carlo price."),
    "surface": ("A relief map. Across is the strike, down is time to expiry, and colour is the height: implied volatility.",
                "One look shows the smile at every expiry at once, steepest for short-dated options."),
    # Results evidence
    "proof1": ("Like copying a song perfectly by ear, yet naming the wrong instruments.",
               f"The optimizer reproduced the prices almost exactly, but the settings it found scored "
               f"{CB['mean_median_skill']:.2f}, where 1.00 is always guessing the typical value."),
    "proof2": ("Different magnets can raise the same ferrofluid surface.",
               f"On {SHARE * 100:.0f}% of real surfaces, more than one set of settings priced the options equally well, and "
               f"those sets were {RATIO:.1f} times as far apart as two random guesses."),
    "hist": ("Many witnesses describe the same car. If they agreed, every bar would sit near zero.",
             "Bars far to the right are surfaces whose equally good fits disagreed a lot."),
    "params": ("Some things every thermometer agrees on, like the room's temperature. Others you can't read off the room "
               "at all, like how fast it would cool if the heating went off.",
               "Today's level (v₀) is pinned down by prices; the speeds back to normal (κ) are not."),
    "magnets": ("Two people can draw the same smile with different pens.",
                "Bharti Airtel's 39-day options were fitted equally well by two very different sets of ten settings."),
    "part": ("Two maps that match street for street in the town centre but disagree about the countryside nobody visits.",
             "Where options trade, the two fits agree. Beyond them, where no price can check them, they part."),
    "six": ("Six different recipes that bake the same cake.",
            "Where the spikes bunch, the prices pin that setting down; where they scatter, they don't."),
    "stock": ("A scale that weighs you correctly every morning but reports a different height each day.",
              "The price error stays small day after day while the distance between equally good fits stays large."),
    "heldout": ("A student who did well on the practice papers but slipped in the real exam.",
                f"On 8 later dates the ANN's prices were off by {G8['median_network_relative'] * 100:.1f}%, against "
                f"{G8['median_best_fit_relative'] * 100:.1f}% for the best possible fit."),
    "backtest": ("A new gadget that beats the old ruler about one day in twenty.",
                 f"With the ANN's settings, Double Heston priced better than a same-day Black–Scholes fit on {BEAT_BS_NUM} of stock-days."),
    "pinn": ("A student who also has to obey the textbook, not just copy past answers.",
             f"On real NIFTY options the physics-informed calibrator was off by {PINN_NIFTY['ft_3']:.2f} volatility points, "
             f"against {PINN_NIFTY['bs']:.2f} for Black–Scholes, and was the best model on {PINN_NIFTY_BEST} of 10 days."),
}

# every result: which way is good news, and an everyday picture of it (keys are RESULTS names)
RESULT_INFO = {
    "Double Heston against one flat volatility": ("higher", "A tailored suit against one size fits all.",
        f"On a typical surface the best Double Heston fit had {FLAT_BETTER * 100:.0f}% less price error, and it was ahead on all 2,400."),
    "Fitting simulated prices": ("lower", "Tracing a drawing so closely you can't see the original underneath.",
        "The optimizer's prices matched the simulated ones almost exactly."),
    "Reading the settings back": ("lower", "Copying a song perfectly by ear, yet naming the wrong instruments.",
        f"{CB['mean_median_skill']:.2f} means the recovered settings were further off than always guessing the typical value (1.00)."),
    "Several equally good fits": ("lower", "Different magnets, same ferrofluid surface.",
        f"{SHARE * 100:.0f}% of real surfaces had more than one equally good set of settings."),
    "How far apart they sat": ("lower", "Two maps that agree on every street but put the landmarks in very different places.",
        f"Equally good fits sat {RATIO:.1f} times as far apart as two random sets of settings."),
    "Today's level": ("lower", "The room temperature: every thermometer agrees on it.",
        "Equally good fits agreed on today's level more closely than random settings would."),
    "Speeds back to normal": ("lower", "Judging how fast a spring snaps back from one photo of it at rest.",
        "Prices barely depend on the speed, so equally good fits put it almost anywhere."),
    "ANN, reading the settings": ("lower", "A student who learned from worked examples and plays safe by answering near the average.",
        f"{NET['mean_skill']:.2f} beats always guessing (1.00) and the optimizer ({CB['mean_skill']:.2f}), mostly by reading today's level well."),
    "ANN on dates it never saw": ("lower", "Good on the practice papers, worse in the real exam.",
        f"On new dates its prices were off by {G8['median_network_relative'] * 100:.1f}%, about four times the best possible fit."),
    "ANN settings against Black–Scholes": ("higher", "A new gadget that beats the old ruler about one day in twenty.",
        "Reading the settings from prices didn't make Double Heston better than the simplest model most of the time."),
    "Next day, against Black–Scholes": ("higher", "Yesterday's forecast, judged on today's weather.",
        "Settings carried to the next day beat Black–Scholes carried forward about one day in five."),
    "PINN fidelity": ("lower", "A student who also has to obey the textbook.",
        "Its prices match the exact formula to about 0.1 volatility points."),
    "PINN, controlled test": ("higher", "Three runners, forty races, the same finishing order every time.",
        "The PINN beat a refitted one-factor Heston on every surface, and Heston beat Black–Scholes."),
    "PINN calibrator on NIFTY": ("lower", "Measured like a thermometer's error, in volatility points.",
        f"{PINN_NIFTY['ft_3']:.2f} points against {PINN_NIFTY['bs']:.2f} for Black–Scholes, on quotes it never saw."),
    "PINN against ANN (demonstration)": ("lower", "Two students, the same lessons; one also had to obey the textbook.",
        "The one that obeyed the pricing equation was about seven times more accurate and priced nothing impossible."),
}
assert set(RESULT_INFO) == {r[0] for r in RESULTS}, "every result needs a direction and an explanation"
RESULTS_DIRECTION = "▲ means a higher number is better news, ▼ a lower one. Open “Explain simply” on any row for an everyday picture."
KEY_BETTER = ["higher", "lower", "", ""]  # beat-rate, PINN vs BS, 99% (a finding, not a score), 3.9× (ditto)


# ================================================================== simpler wording (branch simple-text)
# The same pages, sections and numbers, reworded for readers who have just finished class 12: short sentences,
# one idea each, "jumpiness" for volatility, one everyday picture per hard idea. Every number below is still
# computed from the verified data above; only the words around it change. Source: the "Double Heston site,
# simpler text" doc. Home's physics-only text sits with the PINN block above.
PAGES = [
    ("home", "index.html", "Home", "the physics behind it"),
    ("market", "market.html", "Market", "real NSE prices"),
    ("model", "model.html", "The model", "price an option"),
    ("maths", "how-it-works.html", "How it works", "the equations"),
    ("results", "results.html", "Results", "what we found, every number"),
    ("about", "about.html", "About", "video, method, limits"),
    ("team", "team.html", "Team", "who built it"),
    ("references", "references.html", "References", "papers and data"),
]

# ------------------------------------------------------------------ market
MARKET_SUB = (f"The daily charts start on {FIRST_DAY}. Up to {LAST_DAY} they use NSE's official closing prices; after "
              "that, daily prices from Upstox, up to today. While the market is open, the prices, today's candle and "
              "the day's figures are live.")
LIVE_CLOSED = "The market is closed. Showing the last traded price."
LIVE_FALLBACK = "Live prices aren't available right now. These are NSE's last closing prices."
UNIVERSE = ("NIFTY 50, NIFTY BANK, and the 40 most traded shares that have options. Every share we show an implied "
            "volatility for is on this list.")
WATCH_HEAD, WATCH_NOTE, COVERS_HEAD = "Your list", "Click a name to see its chart", "What this site covers"

# ------------------------------------------------------------------ price an option
MODEL_LEAD = ("Pick a real option on NIFTY, NIFTY BANK or one of 40 big NSE shares. Price it with Double Heston, and "
              "compare it with what the market actually paid. "
              "Move any of the ten settings and the price updates straight away.")
MODEL_EXPLAIN = (f"The model starts out assuming the price jumps about 20% a year. On {LAST_DAY} the market was expecting "
                 f"only about {K['market_iv']:.1f}%, so the model asks for more. Lower today's jumpiness (v₀) and the gap "
                 "shrinks. There's no \"fit it for me\" button: the Results page explains why a computer can't choose all "
                 "ten settings for you.")
MODEL_SOURCE = (f"Option prices are NSE closing prices on {LAST_DAY}. The expected future NIFTY level is taken from the "
                f"NIFTY October futures price, {inr(K['forward'])}. The interest rate is the RBI 91-day Treasury bill "
                "rate, the same one the research used.")
PRICE_HEADS = {"price": "Our model says", "market": "The market paid", "gap": "Difference", "greeks": "How the price reacts",
               "sliders": "The slow part", "sliders-fast": "The fast part", "smile": "The smile for this expiry",
               "chain": f"Every strike for {EXPIRY}"}
GREEKS_NOTE = "Each number shows how the model's price changes when one thing moves, at your settings."
GREEK_UNITS = {"Delta": "₹ the option moves per ₹1 move in the share or index", "Gamma": "how much that changes per ₹1",
               "Vega": "₹ per 1 point more expected jumpiness", "Theta": "₹ lost each day as expiry nears",
               "Rho": "₹ per 1 point higher interest rate"}
SLIDERS = [
    ("slow", "v₀", "Today's jumpiness", 0.02, 0.0005, 1.0), ("slow", "κ", "Speed back to normal", 0.5, 0.1, 10.0),
    ("slow", "θ", "Normal jumpiness", 0.02, 0.0005, 1.0), ("slow", "ξ", "Jumpiness of the jumpiness", 0.3, 0.05, 2.0),
    ("slow", "ρ", "Link to price", -0.7, -0.99, 0.99),
    ("fast", "v₀", "Today's jumpiness", 0.02, 0.0005, 1.0), ("fast", "κ", "Speed back to normal", 5.0, 0.1, 10.0),
    ("fast", "θ", "Normal jumpiness", 0.02, 0.0005, 1.0), ("fast", "ξ", "Jumpiness of the jumpiness", 0.5, 0.05, 2.0),
    ("fast", "ρ", "Link to price", -0.7, -0.99, 0.99),
]
FELLER = {"slow": "Can touch zero: 2κθ = 0.02 is below ξ² = 0.09", "fast": "Can touch zero: 2κθ = 0.20 is below ξ² = 0.25"}
FELLER_OK = "Can't touch zero: 2κθ = {lhs} is above ξ² = {rhs}"  # after a reprice, with the new numbers
FELLER_FAIL = "Can touch zero: 2κθ = {lhs} is below ξ² = {rhs}"
FELLER_NOTE = ("At these settings, either part's jumpiness can touch zero. That's allowed: the simulator simply stops it "
               "at zero, so prices stay valid.")
CHAIN_NOTE = ("Each row is one strike price. The call and put columns are NSE closing prices. IV is the jumpiness those "
              "prices imply. The model columns are Double Heston at your settings. Click a row to price that strike.")

# ------------------------------------------------------------------ how it works
MATHS_INTRO = ("An option's price depends on how jumpy the share will be before the option expires. Black–Scholes assumes "
               "the jumpiness never changes. Double Heston (2009) lets it change, and splits it into two parts that move "
               "on their own: a fast part for sudden scares and a slow part for long moods. Below is the whole model, one "
               "formula at a time, each with an everyday picture.")
BEND_HEAD = "A ruler can't draw a smile"
BEND = ("Black–Scholes uses the same jumpiness for every strike, so its line is flat, like a line drawn with a ruler. Real "
        "prices bend: insurance against a fall costs more than a bet on a rise. In Double Heston, jumpiness tends to rise "
        "when prices fall, so its line bends the same way.")
FORMULAS_LEDE = ("Each card shows the formula, what its letters mean, and what it does. Hover over the triangle for an "
                 "everyday picture.")
FORMULAS = [
    ("price", "The price is pushed around by two kinds of jumpiness", EQ_PRICE,
     "In each tiny moment, the share price drifts up a little (interest rate minus dividend) and gets two random kicks. "
     "How big each kick is depends on one of the two jumpiness levels.",
     [("S", "share price"), ("r", "interest rate"), ("q", "dividend"), ("v₁, v₂", "the slow and fast jumpiness"),
      ("dW₁, dW₂", "two separate random kicks"), ("dt", "a tiny step of time")]),
    ("variance", "Each kind of jumpiness drifts back to normal", EQ_VAR,
     "Each jumpiness is pulled back toward its normal level (theta, θ) at a speed (kappa, κ), while being shaken at "
     "random by an amount (xi, ξ). Its shakes are linked to the price's kicks by rho (ρ). When rho is negative, falls come "
     "with rising jumpiness. That is what tilts the smile.",
     [("vᵢ", "today's jumpiness of part i"), ("θᵢ", "its normal level"), ("κᵢ", "how fast it returns"),
      ("ξᵢ", "how hard it gets shaken"), ("dZᵢ", "its own random kick"), ("ρᵢ", "the link between price and jumpiness"),
      ("i", "1 for the slow part, 2 for the fast one")]),
    ("cf", "Two separate parts multiply", EQ_CF,
     "Phi (φ) is a short \"fingerprint\" of everywhere the price could end up. The two parts don't depend on each other, "
     "so the model's fingerprint is just the two fingerprints multiplied. That keeps pricing fast.",
     [("φ(u)", "the model's fingerprint"), ("φ₁, φ₂", "each part's own fingerprint")]),
    ("call", "One integral gives the price", EQ_CALL,
     "A call is worth what you expect to receive above the strike, minus what you expect to pay, converted back into "
     "today's rupees. P₂ is the chance the option ends up worth using; P₁ is the same chance counted in shares. Both come "
     "out of the fingerprint through one integral. Our code uses a safer version of the 1993 formula that doesn't break "
     "for long-dated options.",
     [("C", "call price"), ("F", "expected future share price"), ("K", "strike"), ("T", "time to expiry, in years"),
      ("e^(−rT)", "converts to today's rupees"), ("P₁, P₂", "the two chances"), ("Re", "real part of a complex number")]),
    ("mc", "Check it by simulation", "C ≈ e^(−rT) · (1/N) Σₙ max(S_T⁽ⁿ⁾ − K, 0)",
     f"The slow way to the same answer: play out 20,000 possible futures for the price and both jumpiness levels, average "
     f"what the call pays at the end, and convert to today's rupees. For the NIFTY {inr(K['strike'], 0)} call this gives "
     f"₹{inr(K['mc'])} ± {K['mc_se']:.2f}, against ₹{inr(K['dh'])} from the formula: inside the simulation's own margin "
     "of error.",
     [("N", "number of futures played out, 20,000"), ("S_T⁽ⁿ⁾", "the share price at expiry in future n"),
      ("max(S − K, 0)", "what a call pays at expiry")]),
    ("feller", "When jumpiness can't touch zero", EQ_FELLER,
     "If 2κθ is bigger than ξ², that part's jumpiness never reaches zero. Real markets often break this rule. When a "
     "simulated jumpiness would go below zero, our simulator holds it at zero for that step, so prices stay valid.",
     [("κᵢ, θᵢ, ξᵢ", "the speed, normal level and shake of part i")]),
]
FORMULAS = [(k, t, plain, what, [(sym, m[:1].upper() + m[1:]) for sym, m in syms]) for k, t, plain, what, syms in FORMULAS]
SETTINGS_LEDE = ("Each of the two parts has the same five settings, so the model has ten. Here is what each one controls "
                 "and what turning it up does. The starting values are the ones Price an option opens with.")
SETTINGS = [
    ("v₀", "Today's jumpiness", "How jumpy the share is right now. 0.02 means about 14% a year.",
     "Options cost more now, short-dated ones most.", "0.02", "0.02"),
    ("θ", "Normal jumpiness", "The level jumpiness settles back to.", "Long-dated options cost more.", "0.02", "0.02"),
    ("κ", "Speed back to normal", f"How fast jumpiness calms down after a shock. Half of a shock is gone in {SLOW_HL} for "
     f"the slow part and {FAST_HL} for the fast one.", "Shocks fade faster, so this part matters less for long-dated options.",
     "0.5", "5.0"),
    ("ξ", "Jumpiness of the jumpiness", "How much the jumpiness itself jumps around.",
     "The smile curves more: options far from today's price cost more.", "0.3", "0.5"),
    ("ρ", "Link to price", "Whether jumpiness rises when the price falls (negative) or rises (positive). Runs from −1 to 1.",
     "Closer to −1: insurance against falls gets dearer, so the smile tilts more.", "−0.7", "−0.7"),
]
SETTINGS_UP = "Turn it up:"
FACTORS_HEAD = "Two clocks: one fast, one slow"
TWO_CLOCKS = ("Each part is a jumpiness that gets knocked about and then calms down. One calms down slowly and one "
              "quickly. That lets the model price next week's options and next year's options differently.")
FACTORS = (f"Each part gets knocked about and drifts back to its normal level. The fast one (κ 5.0) loses half of any "
           f"shock in {FAST_HL}. The slow one (κ 0.5) takes {SLOW_HL}.")
SKEW_NOTE = ("How much more insurance against a fall costs than a bet on a rise, in volatility points. That extra cost "
             "shrinks the further away the expiry is.")
FAN_NOTE = (f"60 of 400 simulated one-year paths, all starting at 100. The shading covers the middle 50% and the middle 90% "
            f"of the 400. The same simulator checks our calculator: 20,000 paths price the NIFTY {inr(K['strike'], 0)} call "
            f"at ₹{inr(K['mc'])} ± {K['mc_se']:.2f}, against ₹{inr(K['dh'])} from the formula.")
SURFACE_NOTE = (f"Implied volatility for every strike and every expiry, at the starting settings. Low strikes, which are "
                f"insurance against falls, carry the most. The tilt is steepest for options that expire soon: "
                f"{_S1M[0]:.1f}% down to {_S1M[-1]:.1f}% across strikes at one month, and {_S1Y[0]:.1f}% to "
                f"{_S1Y[-1]:.1f}% at one year. \"≈ 0\" marks options worth almost nothing, where no volatility can be read.")
MATHS_HEADS = {"factors": "The two parts, moving", "skew": "Why the lopsidedness fades with time",
               "fan": "Many possible futures", "surface": "The whole picture at once", "settings-list": "Five settings for each part"}

# ------------------------------------------------------------------ results
RESULTS_PAGE_HEAD = "It beat the one-number method on every price list we tested. Knowing why takes more than a perfect match."
RESULTS_PAGE_LEDE = ("Everything the project found is on this page. First the win in numbers, then the proof behind it, "
                     "then what our two kinds of neural network did. At the end, every result sits in one table with the "
                     "data it came from. That includes the results that didn't work, because they're how you know the "
                     "ones that did are real.")
KEY_NUMS = [
    (f"{DH_BEAT_ALL * 100:.0f}%", f"of 2,400 real price lists: Double Heston beat one fixed jumpiness on every one, with "
                                  f"{FLAT_BETTER * 100:.0f}% less error on a typical one"),
    (f"{PINN_NIFTY['ft_3']:.2f} vs {PINN_NIFTY['bs']:.2f}", "our PINN against Black–Scholes on real NIFTY options, in volatility points"),
    (f"{SHARE * 100:.0f}%", "of those price lists had several equally good answers: a finding, not a flaw"),
    (f"{RATIO:.1f}×", "how far apart those answers were, compared with two settings picked at random"),
]
EVIDENCE_HEAD = "The proof"
TWIST = "Ask the model which of its ten settings made the bend, though, and the prices can't tell you. Here is how we know."
PROOF1_HEAD = "Test 1: questions where we already knew the answer"
PROOF1 = (f"We made {CB['surfaces_calibrated']} price lists ourselves, from settings we chose, so we knew the right answer. "
          f"Then we asked a standard search program to find those settings again, starting from "
          f"{CB['starts_per_surface']} places each time. It matched the prices almost perfectly: a typical error of "
          f"9.16 × 10⁻⁸. But the settings it found scored {CB['mean_median_skill']:.2f}. On this score 1.00 means \"no "
          "better than always guessing the average\", and lower is better.")
PROOF1_NUMS = [("9.16 × 10⁻⁸", "typical price error"), (f"{CB['mean_median_skill']:.2f}", "how well it found the settings (1.00 = just guessing)"),
               (f"{CB['price_equivalent_subset']['mean_median_skill']:.2f}", f"the same, on the {CB['price_equivalent_subset']['n']} closest price matches")]
PROOF1_NET = (f"Our ANN reads the settings straight from prices. It scores {NET['mean_skill']:.2f} on a related version of "
              f"the same score, where the search program scores {CB['mean_skill']:.2f}. It does better by playing safe and "
              f"staying close to typical values. The one setting it reads well is today's jumpiness (v₀, "
              f"{NET['param_skill']['v0_s']:.2f}).")
PROOF2_HEAD = "Test 2: real NSE prices, no answer assumed"
PROOF2 = (f"We took 2,400 real price lists: NSE's 40 most traded shares over 60 days. For each one, we started the search "
          f"from 16 different places. On {SHARE * 100:.0f}% of them, more than one set of settings matched the prices "
          f"equally well (within 10% of the best match). Those equally good answers were typically "
          f"{AMB['median_dispersion']:.2f} apart, against {RAND:.2f} for two settings picked at random: "
          f"{RATIO:.1f} times as far.")
PROOF2_NUMS = [(f"{SHARE * 100:.0f}%", "of 2,400 price lists had several equally good answers"),
               (f"{RATIO:.1f}×", "further apart than two random picks"),
               (f"{FLAT_BETTER * 100:.0f}%", "less error than one fixed jumpiness, on a typical price list")]
HIST_HEAD = "How far apart the equally good answers were"
PER_PARAM = ("Split by setting, the pattern makes sense. Today's jumpiness (v₀) is pinned down: equally good answers agree "
             "on it more closely than random picks would. The speed back to normal (κ) is not pinned down at all. The best "
             f"answer's speed got stuck at the edge of the allowed range on {NB['kappa_s'] * 100:.0f}% of price lists for "
             f"the slow part and {NB['kappa_f'] * 100:.0f}% for the fast part.")
PAIR_HEAD = "One example: Bharti Airtel"
PAIR_LEDE = (f"Here is Bharti Airtel's price list at the close on 21 Aug 2026, matched twice. Both matches miss the market "
             f"by ₹{PAIR_ERR[0]:.2f} an option on average. But one says a jumpiness shock takes "
             f"{half_life(PA['kappa_s'])} to fade by half. The other says just {half_life(PB['kappa_f'])} to "
             f"{half_life(PB['kappa_s'])}.")
PAIR_MAGNETS = ("Iron filings over hidden magnets: different arrangements of magnets can make the very same pattern. The "
                "prices are the pattern; the ten settings are the hidden magnets.")
PAIR_TYPICAL = (f"This price list had {PAIR['equivalents']} equally good answers out of 16 starts. Their spread, "
                f"{PAIR['median_dispersion']:.2f}, is exactly the typical spread across all 2,400 price lists. So this is "
                "the normal case, not the worst one.")
PAIR_NOTE = ("Each spike's height is that setting's size on its own scale. A star (*) means the setting was pushed against "
             "the upper limit the search was allowed.")
PAIR_PART_HEAD = f"Where people trade, they agree. A year out, they're {PAIR_GAP_1Y:.1f} points apart."
PAIR_PART = (f"That day, Bharti Airtel had options expiring in 4 days and 39 days. Both answers price those alike. Now ask "
             f"them about a one-year option, which isn't traded. Answer A says {_term('a', 365):.1f}% jumpiness; answer B "
             f"says {_term('b', 365):.1f}%. The prices give no reason to prefer either.")
PAIR_SIX = (f"Bharti Airtel, 21 Aug 2026: 16 starts gave {PAIR['equivalents']} answers within 10% of the best price error. "
            "Each spike is one answer. Where the spikes bunch together, the prices pin that setting down. Where they "
            "scatter, they don't.")
RESULTS_HEADS = {"pool": "Bharti Airtel, 39-day options", "magnets": "The ten settings of each answer",
                 "six": "All six equally good answers", "stock": "One share, day by day",
                 "heldout": "The ANN on days it had never seen", "backtest": "The ANN against Black–Scholes",
                 "pinn": "The PINN on real NIFTY options", "results": "Every result", "data": "The data",
                 "terms": "What the words mean"}


def _rel_line():
    import statistics
    dh = statistics.median(r[1] for r in REL_STOCK) * 100
    fl = statistics.median(r[2] for r in REL_STOCK) * 100
    ds = statistics.median(r[3] for r in REL_STOCK)
    return (f"Take RELIANCE. Its best Double Heston match beat one fixed jumpiness on all 60 of its days. The typical "
            f"error was {dh:.2f}% of the share price, against {fl:.2f}%. On the same days, the equally good answers sat "
            f"a typical {ds:.1f} apart.")


REL_LINE = _rel_line()
NN_HEAD = "Two kinds of neural network: an ANN and a PINN"
ANN_TEXT = ("Our ANN is an ordinary neural network. It learns to read the ten settings from prices purely from examples. "
            "It produced the settings behind the 210-share studies on this site.")
PINN_TEXT = ("Our PINNs (physics-informed neural networks) are also trained on the model's own pricing equation, so their "
             "answers must obey the physics, not just copy examples. The Double Heston PINN learned from exact prices "
             "plus the equation at 18,000 points. It matches our exact calculator to 1.1 × 10⁻⁵, about 0.1 volatility "
             "points, on 8,192 points it had never seen. On 40 test price lists it beat the simpler one-part Heston every "
             "time, and Heston in turn beat Black–Scholes.")
HELDOUT = (f"On 8 later trading days it had never seen, the ANN's prices were off by "
           f"{G8['median_network_relative'] * 100:.1f}% on a typical option. The best possible match was off by "
           f"{G8['median_best_fit_relative'] * 100:.1f}%: a gap of {G8['median_gap_pp']:.1f} points.")
BACKTEST = (f"This is a tough contest. Black–Scholes gets re-matched fresh to each day's own prices, while Double Heston "
            f"uses settings our ANN read from that day's quotes. Even so, Double Heston priced the day's options better on "
            f"{BT_SAME_DAY * 100:.1f}% of {BT_PAIRS:,} share-days ({BT_SAME_DAY_N:,} of them). A fairer contest carries "
            f"both models' settings forward one day without updating either. There, Double Heston won on "
            f"{BT_NEXT_DAY * 100:.1f}%.")
PINN_MARKET = (f"We tested it on 10 high-jumpiness days in April 2026: 1,750 NIFTY option prices it had never seen. Our "
               f"PINN was typically off by {PINN_NIFTY['ft_3']:.2f} volatility points. Black–Scholes was off by "
               f"{PINN_NIFTY['bs']:.2f}, and a classical Double Heston search by {PINN_NIFTY['dh_cold']:.2f}. The PINN "
               f"took {PINN_NIFTY_SECONDS[0]:.1f} seconds instead of {PINN_NIFTY_SECONDS[1]:.0f}, and was the best model "
               f"on {PINN_NIFTY_BEST} of the 10 days.")
RESULTS_LEDE = ("All the project's numbers in one place: what we measured, on which data, and whether it is good news. "
                "The results that didn't work are kept, because they are part of the answer.")
RESULTS_DIRECTION = "▲ means a higher number is better news; ▼ means a lower one is. Hover over a triangle for an everyday picture."
_RENAME = {"Double Heston against one flat volatility": "Double Heston against one fixed jumpiness",
           "Fitting simulated prices": "Matching made-up prices", "Reading the settings back": "Finding the settings again",
           "Several equally good fits": "Several equally good answers", "How far apart they sat": "How far apart they were",
           "Today's level": "Today's jumpiness", "ANN, reading the settings": "ANN reading the settings",
           "ANN on dates it never saw": "ANN on days it never saw", "PINN fidelity": "PINN accuracy",
           "PINN calibrator on NIFTY": "PINN on NIFTY", "PINN against ANN (demonstration)": "PINN against ANN (demo)"}
_WHAT = {
    "Double Heston against one fixed jumpiness": "Typical error of the best match on 2,400 real price lists. It was ahead on every one.",
    "Matching made-up prices": f"Typical error of a search program on {CB['surfaces_calibrated']} made-up price lists.",
    "Finding the settings again": "How close it got to the true settings. 1.00 is just guessing; lower is better.",
    "Several equally good answers": "Share of 2,400 real price lists with more than one equally good set of settings.",
    "How far apart they were": f"Typical gap between equally good answers ({AMB['median_dispersion']:.2f}) against two random picks ({RAND:.2f}).",
    "Today's jumpiness": "Gap between equally good answers for the slow part's level, against about 0.95 at random. Pinned down.",
    "Speeds back to normal": "Gap for the slow part's speed, against about 0.90 at random. Not pinned down at all.",
    "ANN reading the settings": f"Score on {NET['test_samples']:,} made-up price lists, against {CB['mean_skill']:.2f} for the search program.",
    "ANN on days it never saw": f"Typical pricing error on 8 later days, against {G8['median_best_fit_relative'] * 100:.1f}% for the best match.",
    "ANN settings against Black–Scholes": f"Share-days where Double Heston with the ANN's settings priced better than a fresh same-day Black–Scholes ({BT_SAME_DAY_N:,} of {BT_PAIRS:,}).",
    "Next day, against Black–Scholes": "Share-days where yesterday's settings beat yesterday's Black–Scholes on today's prices.",
    "PINN accuracy": "PINN's error against the exact calculator on 8,192 unseen points (0.1 volatility points).",
    "PINN, controlled test": "Price lists where the PINN beat one-part Heston, which beat Black–Scholes.",
    "PINN on NIFTY": f"Typical error on 1,750 unseen prices, against {PINN_NIFTY['bs']:.2f} for Black–Scholes. Best on {PINN_NIFTY_BEST} of 10 days.",
    "PINN against ANN (demo)": "Error of two identical networks, with and without the pricing equation.",
}
RESULT_INFO = {_RENAME.get(n, n): v for n, v in RESULT_INFO.items()}
RESULTS = [(_RENAME.get(n, n), v, _WHAT[_RENAME.get(n, n)], verdict) for n, v, _, verdict in RESULTS]
assert set(RESULT_INFO) == {r[0] for r in RESULTS}, "every result needs a direction and an explanation"
DATA_SETS = [
    ("Market charts", f"{N_DAYS} trading days", f"NSE closing prices, {FIRST_DAY} to {LAST_DAY}, for NIFTY 50, NIFTY BANK and the Market page shares."),
    ("NIFTY option prices", f"{len(D['chain'])} strikes", f"NIFTY options expiring {EXPIRY}, at the {LAST_DAY} close, only ones that actually traded."),
    ("Real price lists", "12,480", "210 NSE shares × 60 trading days. 12,600 tried; 120 failed our data checks. Each aims for 20 prices; a typical one has 17."),
    ("Equally-good-answers study", "2,400", "The 40 most traded of those shares over the same 60 days, each searched from 16 starting points."),
    ("Made-up price lists", f"{CB['surfaces_calibrated']}", "Made by our own calculator from settings we chose, so the right answer is known."),
    ("ANN test set", f"{NET['test_samples']:,}", "Made-up price lists the ANN never saw while learning."),
    ("Unseen days", "8 days", "Later trading days the ANN never saw, used to test it on real prices."),
    ("Next-day test", f"{BT_PAIRS:,} share-days", "Every share and every pair of back-to-back trading days: one day's settings used to price the next."),
    ("PINN training", "100,000 + 18,000", "Exact Double Heston prices to learn from, plus points where the pricing equation itself must hold."),
    ("NIFTY, high jumpiness", "10 days, 1,750 prices", "The 10 NIFTY days of 2026 with the highest recent jumpiness, picked by a rule fixed before any testing."),
]
TERMS = [
    ("Price list (option surface)", "All of one share's option prices on one day, across strikes and expiries."),
    ("Setting", "One of Double Heston's ten numbers. Each part has today's level, normal level, speed back to normal, jumpiness of the jumpiness, and link to price."),
    ("Equally good answer", "A set of settings whose error is within 10% of the best one found for that price list."),
    ("Gap between answers", "How far apart two sets of settings are, measured so that every setting counts equally."),
    ("Recovery score", "The error in the settings divided by the error from always guessing the typical value. 1.00 is no better than guessing; lower is better."),
    ("Volatility point", "One percentage point of implied volatility, for example 15% against 16%."),
    ("Share-day", "One share on one trading day."),
    ("Unseen (held out)", "Data kept back while the model was being built, so it can be tested fairly."),
]

# ------------------------------------------------------------------ about, team, references
ABOUT_HEAD = "A B.Tech physics project about one question, and an honest answer."
VIDEO_CAPTION = "A short narrated video about the model and what we found, made from our project report. [Video to be added]"
ABOUT_HEADS = {"video": "The video", "method": "How we did it", "limits": "What the model can't do", "also": "We also looked at"}
METHOD = [
    "Prices come from the Double Heston formula and are double-checked by simulating thousands of possible futures.",
    "The research data is NSE's official end-of-day files. The Results page lists every dataset, its size and what it was used for.",
    "We found and fixed three bugs in our data pipeline, then re-ran every real-market result. We checked each one against "
    "one fixed jumpiness, which a true best match should never lose to.",
]
LIMITS = [
    "It has no sudden jumps, so it still underestimates the biggest one-day moves.",
    "Dividends are possible but set to zero, and one interest rate is used for every expiry.",
    "It ignores trading costs. Real trades pay the gap between the buying and selling price.",
    "End-of-day data has closing prices only, not live buying and selling quotes.",
    "A typical price list has 17 of the 20 prices we aim for (between 10 and 20 on 80% of price lists).",
]
ALSO = ("Can smarter forecasts (called EWMA and GARCH) predict next month's jumpiness better than simply assuming it will "
        "look like last month? We tested this over 60 shares and ten years, always predicting forward in time.")
TEAM = [("[Name]", "Model and calculator"), ("[Name]", "Data"), ("[Name]", "Website and design"), ("[Name]", "Research and report")]
SUPERVISOR_HEAD = "Guide"
THANKS = ["NSE, for the free end-of-day files the research uses.", "Upstox, for the market data behind the live prices.",
          "The people who make NumPy, SciPy and pandas, the free tools we built on."]
REFS_LEAD = "The research papers behind the model and its maths, the history it grew from, and where our data comes from."
FOOTER = (f"Not trading advice. Charts use NSE closing prices up to {LAST_DAY}; prices beside each name are live from "
          "Upstox while the market is open.")

# chart titles and how-to-read lines that the doc reworded
CHART_NOTES = {**CHART_NOTES,
    "smileBend": ("Implied volatility by strike, 30 days to expiry",
                  "Across is the strike, as a percentage of today's price. Up is implied volatility. The dashed line is "
                  "Black–Scholes; the solid line is Double Heston at its starting settings."),
    "marketSmile": ("Market against model, by strike",
                    "Rings are real NSE closing prices, turned into implied volatility. The line is Double Heston at your "
                    "settings. The dotted line marks where NIFTY is today."),
    "candles": ("Daily candles with trading volume",
                "Each candle is one day. The thick part runs from the day's opening price to its closing price; the thin "
                "line from its lowest price to its highest. Green closed higher than it opened, red lower. The bars "
                "underneath show how much was traded. The tag on the right is the last closing price."),
    "indexLine": ("Closing level by day", "One point per trading day. Hover over the line to see the date and level."),
}

# everyday pictures the doc changed to Indian ones
EXPLAIN = {**EXPLAIN,
    "decay": ("A cup of chai and a big kettle, both just boiled. The cup is cold in minutes; the kettle stays warm for "
              "hours. Same rule, different speeds.", f"Half of a shock to the fast part is gone in {FAST_HL}; in the slow part it takes {SLOW_HL}."),
    "fan": ("Like a cyclone forecast cone: tomorrow's path is fairly certain, next month's much less.",
            "The shaded bands show how far simulated prices spread over a year. Averaging what an option pays across "
            "paths like these gives the simulation price."),
    "proof2": ("Iron filings over hidden magnets: different arrangements can make the very same pattern.",
               f"On {SHARE * 100:.0f}% of real price lists, more than one set of settings matched equally well, and those "
               f"sets were {RATIO:.1f} times as far apart as two random picks."),
    "params": ("Every thermometer agrees on how warm the room is now. None of them can tell you how fast it would cool if "
               "the heater went off.", "Today's jumpiness (v₀) is pinned down by prices; the speeds back to normal (κ) are not."),
    "part": ("Two maps that match street for street in the city centre but disagree about the villages nobody visits.",
             "Where options trade, the two answers agree. Beyond them, where no price can check them, they part."),
    "stock": ("A weighing scale that shows your weight correctly every morning but reports a different height each day.",
              "The price error stays small day after day while the gap between equally good answers stays large."),
    "heldout": ("A student who did well on the practice papers but slipped in the board exam.",
                f"On 8 later days the ANN's prices were off by {G8['median_network_relative'] * 100:.1f}%, against "
                f"{G8['median_best_fit_relative'] * 100:.1f}% for the best possible match."),
    "backtest": ("A new gadget that beats a ruler freshly redrawn every morning about one day in twenty.",
                 f"With the ANN's settings, Double Heston priced better than a same-day Black–Scholes on {BEAT_BS_NUM} of share-days."),
}

# ------------------------------------------------------------------ Price an option, on live NIFTY options
PRICE_HEADS = {**PRICE_HEADS, "chain": "Every strike for"}
CHAIN_FIG = "NSE closing prices and the jumpiness they imply, with the model's price for each strike"
CHAIN_FIG_LIVE = "Live NSE prices and the jumpiness they imply, with the model's price for each strike"
CHAIN_NOTE = ("Each row is one strike price. The call and put columns are NSE prices. IV is the jumpiness those prices "
              "imply. The model columns are Double Heston at your settings. Click a row to price that strike.")
MKT_MID, MKT_LAST = "Live quote (halfway between the best buy and sell prices)", "Last traded price"
MODEL_EXPLAIN_LIVE = ("The model starts out assuming the price jumps about 20% a year. Right now the market is pricing "
                      "about {iv}% for this option, so the model asks for more. Lower today's jumpiness (v₀) and the gap "
                      "shrinks. There's no \"fit it for me\" button: the Results page explains why a computer can't choose "
                      "all ten settings for you.")
MODEL_SOURCE_LIVE = ("Option prices are live NSE prices from Upstox, updated every minute: halfway between the best buy "
                     "and sell quotes, or the last trade when there is no quote. The expected future price ({fwd}) "
                     "comes from the call and put prices at the {k} strike. The interest rate is the RBI 91-day Treasury "
                     "bill rate the research used.")
LIVE_HOLIDAY = "NSE is closed today for {day}. Showing the last traded prices."
CHART_NOTES = {**CHART_NOTES, "marketSmileLive": ("Market against model, by strike",
    "Rings are live NSE prices, turned into implied volatility. The line is Double Heston at your settings. The dotted "
    "line marks where the share or index is now.")}

# ------------------------------------------------------------------ Market: today's minute candles
INTRA_TITLE = "Today's {n}-minute candles with trading volume"
INTRA_TITLE_LAST = "{n}-minute candles from the last trading day, {day}"
INTRA_CAP = ("Each candle is {n} minutes of trading: the thick part runs from its opening price to its closing price, the "
             "thin line from its lowest price to its highest. Green closed higher, red lower. The dashed line is the "
             "previous day's close. While the market is open, new candles appear every 30 seconds.")
INTRA_LOADING = "Loading the day's candles…"
INTRA_NONE = "Minute candles aren't available for this name right now."
