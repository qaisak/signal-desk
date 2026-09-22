"""Builds the Encord CA take-home deliverable as a PDF."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Image)

OUT = Path(r"C:\Users\Qais\OneDrive\Career\Encord-CA-Exercise-Qais-Al-Azkawi.pdf")
INK, MUTED, ACC, SOFT, LINE = colors.HexColor("#171a33"), colors.HexColor("#5d6180"), colors.HexColor("#4f46e5"), colors.HexColor("#eeedfb"), colors.HexColor("#dfe2ee")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=18, leading=22, spaceBefore=2, spaceAfter=6, textColor=colors.HexColor("#12143a"))
H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12.5, leading=15, spaceBefore=12, spaceAfter=4, textColor=ACC)
H3 = ParagraphStyle("h3", parent=ss["Heading3"], fontSize=10.5, leading=13, spaceBefore=8, spaceAfter=2, textColor=INK)
B = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.7, leading=13.4, textColor=INK, spaceAfter=5)
SM = ParagraphStyle("sm", parent=B, fontSize=8.3, leading=11, textColor=MUTED)
EYE = ParagraphStyle("eye", parent=B, fontSize=8, leading=10, textColor=ACC, spaceAfter=2)
MAIL = ParagraphStyle("mail", parent=B, fontName="Helvetica", fontSize=9.2, leading=13, leftIndent=8, rightIndent=8, spaceAfter=7)
SUBJ = ParagraphStyle("subj", parent=MAIL, fontName="Helvetica-Bold", textColor=colors.HexColor("#12143a"), spaceAfter=5)


def P(t, st=B): return Paragraph(t, st)
def bullets(items, st=B): return [Paragraph(f"&bull;&nbsp;&nbsp;{t}", ParagraphStyle("bl", parent=st, leftIndent=9, spaceAfter=3)) for t in items]
def rule(): return HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=6, spaceAfter=6)


def email(subject, body, note=None):
    """A drafted email in a boxed panel."""
    cell = [Paragraph(f"Subject: {subject}", SUBJ)]
    for para in body.strip().split("\n\n"):
        cell.append(Paragraph(para.replace("\n", "<br/>"), MAIL))
    t = Table([[cell]], colWidths=[168 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SOFT), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                           ("LINEBEFORE", (0, 0), (0, -1), 2, ACC)]))
    out = [t]
    if note: out.append(P(note, SM))
    out.append(Spacer(1, 6))
    return KeepTogether(out)


def table(data, widths, header=True, size=8.6):
    rows = [[Paragraph(c, ParagraphStyle("c", parent=SM, fontSize=size, leading=size + 2.6, textColor=colors.white if (header and i == 0) else INK,
                                         fontName="Helvetica-Bold" if (header and i == 0) else "Helvetica")) if isinstance(c, str) else c for c in r] for i, r in enumerate(data)]
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.25, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header: style.append(("BACKGROUND", (0, 0), (-1, 0), ACC))
    for i in range(2 if header else 1, len(rows), 2): style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f7f7fc")))
    t.setStyle(TableStyle(style)); return t


S = []

# ------------------------------------------------------------------ cover
S += [P("ENCORD &nbsp;|&nbsp; COMMERCIAL ASSOCIATE (UK) &nbsp;|&nbsp; PRACTICAL EXERCISE", EYE),
      P("Three accounts worth Encord's time, and how I would earn the first meeting", H1),
      P("Qais Al-Azkawi &nbsp;&middot;&nbsp; September 2026", SM), rule()]
S += [P("How I chose", H2),
      P("I scored UK accounts on two things. <b>Fit</b>: how much perception data they generate, how repetitive it is, and whether Encord's modalities match theirs. "
        "<b>Why now</b>: a live event in the last ninety days that creates a labelling need, taken from their own signals rather than a list, namely funding, product launches, "
        "the roles they are hiring and what their engineers publish. I built a small tool to watch those signals daily, which is where the evidence below comes from, "
        "but the judgement of which three to work is mine.")]
S += [P("The three, and why they are different bets", H2)]
S += [table([["Account", "What they build", "Why now (evidence)", "Lead with"],
             ["<b>Dexory</b><br/>London and Wallingford<br/>Warehouse robotics",
              "Autonomous robots scan warehouse racking daily; DexoryView turns it into live inventory and risk alerts, sold per site to 3PLs and large operators",
              "Storage Health launched Feb 2026 (damaged stock, leaning pallets: label classes that did not exist a year ago). $165m Series C. Their board today is four US Sales Directors, an AE, an SDR and a CSM, so sites are multiplying, and one Senior Data Engineer whose remit is modelling perception accuracy per site against contracted SLAs",
              "Index then Annotate"],
             ["<b>Oxa</b><br/>Oxford<br/>Industrial autonomy",
              "A universal AI driver for industrial vehicles in ports, airports and yards, with DHL at Heathrow, bp and Port of Tyne",
              "$103m Series D first close in Mar 2026 with NVIDIA and the National Wealth Fund. SHIFFT launched with Dubai Future Foundation in Aug 2026: a new geography, new climate, new vehicle mix, which means their existing labelled data no longer represents the job",
              "Index then Annotate (3D and video)"],
             ["<b>Proximie</b><br/>London<br/>Surgical video",
              "Connected operating rooms: hardware streams and records surgery, the Intelligence Suite applies computer vision to theatre workflow and utilisation",
              "Sept 2026: the largest ever NHS surgical AI evaluation, 104 operating theatres, with AWS and Deloitte. An evaluation programme lives or dies on consistent ground truth and a defensible way to score models",
              "Annotate (video) then Active"]],
            [26 * mm, 36 * mm, 76 * mm, 24 * mm])]
S += [Spacer(1, 6), P("Deliberately three different sales motions: a curation story where the data is repetitive by design (Dexory), an expansion story where a new site invalidates old data (Oxa), "
                      "and an evaluation story where the scarce resource is clinician time and the blocker is governance (Proximie). If all three worked the same way, I would only be proving one thing.", SM)]

# ------------------------------------------------------------------ account pages
ACCOUNTS = [
    dict(name="Dexory", one="Robots that scan the same racking every day, so the problem is choosing frames, not collecting them",
         why=["<b>New model classes with no labelled history.</b> Storage Health (Feb 2026) detects damaged stock and leaning pallets. Those classes did not exist a year ago, so recall on rare damage is bootstrapped from a small hand-picked set.",
              "<b>Redundancy is structural.</b> A robot images the same rack face on every pass, every day, across every site. Labelling budget is spent on near-duplicates while the rare events stay under-represented. This is the Automotus problem with pallets instead of cars.",
              "<b>Accuracy is now contractual.</b> Their Senior Data Engineer ad describes modelling perception accuracy, scan coverage and obstructions against the SLAs and KPIs committed per site. That is an evaluation problem before it is a labelling problem.",
              "<b>Sites are multiplying.</b> The open roles are a US sales build-out. Every new site is a new distribution: new lighting, new racking, new stock."],
         personas=[("Adrian Negoita, co-founder and CTO", "Owns the technical bet. Right first call at this size of company: one conversation reaches the decision, not a champion who then has to sell internally."),
                   ("Perception and autonomy engineering lead", "Feels the pain daily: rare-class recall, LIDAR plus camera labelling, model regressions per site. Best person to validate the hypotheses and become the champion."),
                   ("Senior Data Engineer (role open now)", "Explicitly hired to model perception accuracy per site against SLAs. Whoever fills it inherits the problem Encord Active solves, and will be looking for tooling in their first month."),
                   ("Oana Jinga, co-founder and Chief Commercial & Product Officer", "The escalation path if engineering stalls: she owns the customer promise that the accuracy number underwrites.")],
         opener=("Storage Health labelling", """Hi Adrian,

Congratulations on Storage Health. Damage and lean detection means new label classes on a stream where most frames are another pass down the same aisle.

Encord sits on your own storage, scores every frame for uniqueness and quality, and shows which frames are worth a labeller before anyone opens one. Automotus, who run fixed street cameras with the same repetition problem, cut their dataset 35% and gained 20% mAP.

I ran the same method on a simulated warehouse-robot stream: 61% fewer frames to label, 95% of racks still covered.

Worth twenty minutes to see whether it holds on your data?

Qais"""),
         note="Sent Tuesday morning. Plain text, no images or tracking pixels, one ask, under 120 words. The numbers do the persuading; the last line asks for time, not a demo."),
    dict(name="Oxa", one="A universal driver only stays universal if the training data keeps up with each new site",
         why=["<b>A new geography invalidates the old data.</b> SHIFFT with Dubai Future Foundation (Aug 2026) adds heat haze, glare, different vehicles and different markings to a dataset dominated by UK routes. The question of what actually needs relabelling is exactly a curation question.",
              "<b>Fixed routes are the most repetitive data there is.</b> The same yard, the same corner, hundreds of times. Their own October 2025 post on multimodal search suggests they already feel the find-the-right-clip problem.",
              "<b>Fresh capital and a productisation push.</b> $103m Series D first close in March 2026 with NVIDIA, and Oxa Foundry positioned as a toolchain, which means buying tooling is culturally acceptable rather than a defeat.",
              "<b>Safety cases need evidence.</b> Selling autonomy into ports and airports means proving perception performance to an operator, not just to yourself."],
         personas=[("Paul Newman, CTO and President", "Founder, Oxford professor, sets the technical direction. Will engage on the intellectual argument about data selection, and is the one person who can make buying tooling acceptable."),
                   ("Graeme Smith, Chief Product Engineering Officer", "Owns engineering, solutions and delivery. His problem is repeatability across sites, which is the commercial framing of the same thing."),
                   ("Perception or data platform lead", "Owns Foundry's data path. The person who will judge whether Index complements what they have built or duplicates it. The honest answer is complements, and saying so early is the credibility move.")],
         opener=("SHIFFT and the new-site data question", """Hi Paul,

SHIFFT puts the driver into a new climate and a new vehicle mix. The hard part is usually deciding which of the new site's frames are genuinely new versus another pass down a route you have already covered.

Encord Index reads your buckets in place, embeds every frame, and makes that gap visible before anything goes to a labeller. Then the same platform labels 3D and video together, and slices model failures by site and condition.

Teams doing this typically label a third less. Curious how Foundry handles it today, and whether there is a gap worth twenty minutes.

Qais"""),
         note="Sent to the CTO because at Oxa the technical argument is the commercial one. The last line concedes they may already have this covered, which is what earns the reply."),
    dict(name="Proximie", one="A 104-theatre evaluation is a ground-truth problem before it is an AI problem",
         why=["<b>The evaluation itself creates the need.</b> Comparing AI across 104 theatres with AWS, Deloitte and the NHS requires one consistent ground truth and one scoring view, sliced by trust, camera and procedure. Without that the results are contestable.",
              "<b>Clinician time is the scarce input.</b> Over 100 terabytes of surgical video, and the only people who can label it are surgeons. Choosing which minutes to annotate matters far more than annotation speed.",
              "<b>Governance is the blocker, and it is Encord's strongest answer.</b> Patient video cannot be copied into a vendor cloud. Encord registers data in the customer's own storage, holds SOC2 Type II, HIPAA and GDPR, and already works with Philips and Harvard Medical School under the same constraints.",
              "<b>No ML hiring visible.</b> A small internal team carrying a very large programme is the classic moment to buy rather than build."],
         personas=[("Richard Carter, CTO", "Owns the platform and the build-versus-buy call on data tooling. Verify the title on LinkedIn before sending: my source is secondary."),
                   ("Head of AI or clinical AI lead", "Owns model performance and the evaluation methodology. The person for whom Active is the product, not Annotate."),
                   ("Dr Nadine Hachach-Haram, founder and CEO", "A practising surgeon; the programme is her credibility. Reserve for a referral or an event, not a cold first touch."),
                   ("Information governance or security lead", "Not the buyer, but the person who can kill it. Bring the data-stays-in-your-bucket story to them early rather than defending it late.")],
         opener=("104 theatres and one ground truth", """Hi Richard,

The NHS evaluation with AWS and Deloitte is a serious undertaking. Multi-site, multi-vendor evaluations usually stall on the same two things: one ground truth everyone accepts, and one scoring view that slices results by trust, camera and procedure.

Encord does both on surgical video, reading from your own storage so nothing leaves your environment. Philips and Harvard Medical School work with us under the same governance constraints; Harvard cut annotation from days to minutes.

Would a twenty-minute compare-notes on how you are handling ground truth be useful?

Qais"""),
         note="No product pitch in the first line. For a clinical audience the credible opener is method, not features, and naming Philips and Harvard does more than any claim about accuracy."),
]

for a in ACCOUNTS:
    S += [PageBreak(), P(f"ACCOUNT &nbsp;|&nbsp; {a['name'].upper()}", EYE), P(a["one"], H1), rule()]
    S += [P("Why they are a fit for Encord right now", H2)] + bullets(a["why"])
    S += [P("Who I would contact, and why", H2)]
    S += [table([["Persona", "Why them"]] + [[f"<b>{n}</b>", w] for n, w in a["personas"]], [58 * mm, 104 * mm])]
    S += [P("First touch", H2)]
    S += [email(a["opener"][0], a["opener"][1], a["note"])]

# ------------------------------------------------------------------ part two
S += [PageBreak(), P("PART TWO", EYE), P("The full sequence for Dexory, until they say yes or no", H1), rule()]
S += [P("Principles I am working to", H2)]
S += bullets([
    "<b>Nine touches over six weeks, then stop.</b> Most replies come after touch four. Stopping cleanly is what makes it possible to come back next quarter without being the person who never went away.",
    "<b>Four channels, not one.</b> Email, LinkedIn, phone, and an event. A sequence that is only email is easy to ignore; the same name arriving three ways is a person, not a campaign.",
    "<b>Three people, not one.</b> Start with the CTO, add the perception lead in week two, add the commercial founder only if engineering goes quiet. Multithreading is how a deal survives one person's inbox.",
    "<b>Every touch carries something, or it does not get sent.</b> A number, a piece of analysis, an invitation. Never just a bump.",
    "<b>Cadence widens as it goes.</b> Days 1, 3, 8, 12, 18, 25, 33, 42. Tight at the start when the trigger is fresh, slower later so it reads as persistence rather than pressure.",
])
S += [P("The sequence", H2)]
S += [table([["#", "Day", "Channel", "Who", "What it carries"],
             ["1", "Tue, day 1", "Email", "CTO", "Storage Health opener with the 61% number and the Automotus result"],
             ["2", "Thu, day 3", "LinkedIn", "CTO", "Connection request, no pitch, one line referencing the same launch"],
             ["3", "Tue, day 8", "Email", "CTO", "The reply-to-self: one specific thing I noticed in their own job ad, the per-site SLA line"],
             ["4", "Mon, day 12", "Email + attachment", "Perception lead", "A different person, a different angle: a one-page teardown of how I would curate a robot pass, with the ontology"],
             ["5", "Wed, day 14", "Phone", "Perception lead", "A call, mid-morning. If voicemail, one sentence and the promise of an email in five minutes, then send it"],
             ["6", "Mon, day 18", "Email", "Both", "Invitation to the physical-AI dinner we run in London, no obligation to buy anything"],
             ["7", "Tue, day 25", "LinkedIn message", "Perception lead", "Share something useful and unrelated to us: a paper or benchmark on rare-class recall"],
             ["8", "Wed, day 33", "Email", "Commercial founder", "Escalation, framed commercially: the accuracy number their customers are promised"],
             ["9", "Thu, day 42", "Email", "CTO", "The permission-to-close email. One line, easy to answer, genuinely ends it"]],
            [8 * mm, 22 * mm, 28 * mm, 26 * mm, 84 * mm])]

S += [PageBreak(), P("The content of each touch", H2)]
S += [P("Touch 1, day 1, email to the CTO", H3)]
S += [email("Storage Health labelling", ACCOUNTS[0]["opener"][1])]

S += [P("Touch 2, day 3, LinkedIn connection request", H3)]
S += [email("(connection note, 280 characters)", """Andrei, I have been reading about Storage Health. I work on the data side of computer vision at Encord and I ran a small experiment on warehouse-robot imagery that I think is relevant to the new classes. No pitch attached to this request, happy to just be connected.""",
            "Sent two days after the email so the name is already familiar. Requests with a specific reason are accepted far more often than blank ones, and acceptance alone tells me the email was at least read.")]

S += [P("Touch 3, day 8, reply on my own thread", H3)]
S += [email("Re: Storage Health labelling", """Hi Adrian,

One more thing that made me think Encord is relevant to you specifically. Your Senior Data Engineer ad talks about modelling perception accuracy, scan coverage and obstructions against the SLAs you have committed per site.

That is the half of this people usually solve last. Encord Active takes your model's predictions and slices accuracy by site, class and scan condition, so the SLA number is produced by the same system that decides what to label next.

If the right person for that is not you, could you point me to them?

Qais""", "Replying on the same thread rather than starting a new one keeps the context visible. The ask is deliberately smaller than a meeting: a name is an easy yes, and a referral inside the company beats a cold email to the same person.")]

S += [P("Touch 4, day 12, email to the perception lead, with a one-page attachment", H3)]
S += [email("How I would curate a Dexory rack pass", """Hi [name],

I did a small piece of work on this rather than send you a deck. One page attached.

I took public dense-shelf imagery, simulated three robot passes per rack with camera offset and exposure drift, and added 10% degraded frames. Then quality gates, embedding de-duplication and diversity sampling: 61% fewer frames to label, 95% of racks still represented, and a detector trained on the curated pick beat a random pick of the same size, 0.48 against 0.43 mAP50.

The page also has a starting ontology for Storage Health: lean as a polyline rather than a box, damage as a mask, scan condition as a frame tag so failures can be correlated with glare and motion blur.

Tell me where I have it wrong. That is genuinely the more useful outcome.

Qais""", "The strongest touch in the sequence, and the reason the sequence exists. It goes to a different person, it contains work rather than claims, and it invites correction. Engineers answer that when they ignore everything else.")]

S += [P("Touch 5, day 14, phone call", H3)]
S += [email("(voicemail, fifteen seconds)", """Hi [name], it is Qais from Encord. I sent you a page on Monday about curating rack passes for the Storage Health classes, including an ontology proposal. I will not call again this week, but I will send you a two-line summary in five minutes in case the attachment was easier to ignore than to open. Thanks.""",
            "Two days after the attachment lands, mid-morning. The voicemail promises a follow-up email and then delivers it within five minutes, which is the only reliable way to make a voicemail useful.")]

S += [P("Touch 6, day 18, invitation", H3)]
S += [email("Dinner with physical-AI teams, London, [date]", """Hi Adrian, [name],

We host a small dinner in London for teams building perception into physical products. Next one is [date]: eight or nine people, robotics, autonomy and medical imaging, no presentations.

The recurring conversation is the one you are living through: how to know which data is worth labelling when a fleet generates more of it every day.

You are both welcome, whether or not Encord is ever useful to you. Shall I hold two places?

Qais""", "Encord runs these dinners and they are a genuine channel rather than a pretext. The value is unconditional and the ask is trivial, which is why this touch often revives a dead thread.")]

S += [P("Touch 7, day 25, LinkedIn message to the perception lead", H3)]
S += [email("(LinkedIn, no ask)", """Saw this and thought of your rare-class problem: [link to a paper or benchmark on long-tail recall in detection]. The section on sampling strategy is the interesting part.

Nothing needed from you. If the Storage Health classes ever become a labelling bottleneck, you know where I am.""",
            "A touch with no ask at all, in a different channel. It keeps the name alive without cost to them, and it is the last light touch before the sequence escalates.")]

S += [P("Touch 8, day 33, email to the commercial founder", H3)]
S += [email("The accuracy number behind the SLA", """Hi Oana,

I have been speaking to your engineering side about how Dexory chooses which scan data to label. I wanted to put the commercial version of it in front of you.

Storage Health makes a promise to a customer about damage and rack compliance. The confidence in that promise comes from labelled data, and today most labelling budget on a daily-scan fleet goes into near-duplicate frames of racks you have already seen.

On a proxy of that data we cut the frames needing labels by 61% and improved model accuracy at the same budget. For a fleet at your scale that is both a cost line and a defensibility line.

Twenty minutes with whoever owns that trade-off?

Qais""", "The escalation, six weeks in, and the only touch framed as money and risk rather than engineering. Note it says openly that I have been talking to their team: pretending otherwise is how you lose both.")]

S += [P("Touch 9, day 42, the permission-to-close email", H3)]
S += [email("Closing the file", """Hi Adrian,

I have not managed to land this one with you, which usually means the timing is wrong rather than the idea.

I will stop here. If labelling volume or per-site accuracy becomes a problem when the next wave of sites goes live, reply to this email and I will pick it straight back up.

One thing worth keeping either way: curate before you label, not after. It is the cheapest change available to a fleet that scans the same racks daily.

Thanks for the time you did give me.

Qais""", "Genuinely the last one. It gives them an easy out, leaves something useful behind, and makes a re-approach next quarter welcome rather than tiresome. Break-up emails reliably out-reply the touches before them, which is why this one is written to be answered rather than to guilt anyone.")]

# ------------------------------------------------------------------ responses
S += [PageBreak(), P("What I do when they respond", H2)]
S += [table([["Response", "What I do"],
             ["<b>Yes, book a call</b>", "Confirm within the hour with an agenda of three questions, not a demo plan: what fraction of frames reach a labeller today, who reviews the edge cases, and who owns the labelling budget. Send the Dexory brief the day before so the call is a conversation, not a presentation. Bring a solutions engineer if the ontology comes up."],
             ["<b>Interested but not now</b>", "Get the reason and the date. Park them in the desk with a follow-up set for that date, and keep two light touches in between: their next launch, and the dinner. A no-for-now that is diarised is worth more than a maybe."],
             ["<b>We have this in-house</b>", "Believe them, and ask what they built and where it creaks. Most teams have curation scripts but no evaluation loop. Reposition on Active rather than arguing about Index, and ask for twenty minutes with whoever owns model evaluation."],
             ["<b>Not interested, no reason</b>", "One reply, one question: is it timing, budget or the wrong person? Then stop. Log the reason in the account so nobody on the team repeats the sequence in three months."],
             ["<b>Silence through all nine</b>", "Close the file, set a trigger rather than a date: next funding round, next product launch, or a perception role opening. The desk surfaces it when it happens and the next opener writes itself."]],
            [34 * mm, 128 * mm])]

S += [P("What I would measure", H2)]
S += bullets([
    "<b>Meetings booked per hundred accounts worked</b>, not emails sent. Volume is an input, not a result.",
    "<b>Reply rate by touch number</b>, so I learn which touch is carrying the sequence and cut the ones that are not.",
    "<b>Reply rate by persona</b>: if the perception lead answers three times more often than the CTO, the sequence should start there next time.",
    "<b>Meetings that become qualified opportunities</b>, because booking meetings with the wrong person is an easy number to fake and a hard one to live with.",
    "<b>Reasons for no</b>, written down. Twenty of those is the most useful thing a new CA can hand the team after a month.",
])

S += [P("Assumptions and honest caveats", H2)]
S += bullets([
    "Personas come from public sources: company leadership pages, press coverage and their own job board. I would verify each on LinkedIn before sending, and Proximie's CTO in particular comes from a secondary source.",
    "The 61% and the mAP comparison come from my own experiment on public shelf imagery with simulated robot re-passes, not from Dexory data. Real de-duplication rates will be lower. I would rather say that in the first email than be corrected on the first call.",
    "Encord numbers used here are the published Automotus and Harvard results. I have not invented a customer figure anywhere in this document.",
    "The dinner invitation assumes the London dinners are still running and that I could get two places approved. If not, that touch becomes an introduction to a relevant customer instead.",
], SM)

S += [Spacer(1, 10), rule(), P("Qais Al-Azkawi &nbsp;&middot;&nbsp; qaisqas@gmail.com &nbsp;&middot;&nbsp; The account-watching tool behind the evidence in this document: "
                               "<font color='#4f46e5'>https://qaisak.github.io/signal-desk/</font>", SM)]


# ------------------------------------------------------------------ appendix: the touch-4 attachment
FUNNEL = Path(r"C:\Users\Qais\encord-dexory\outputs\fig_funnel.png")
S += [PageBreak(), P("APPENDIX", EYE), P("The one page attached to touch 4", H1),
      P("Included so the sequence can be judged on what it delivers, not on a promise to deliver something. This is the page that goes to the perception lead on day 12.", SM), rule()]
S += [P("Curating a Dexory rack pass: what I did and what it cost", H2)]
S += [P("<b>The setup.</b> No Dexory data, so I built a proxy. 450 public dense-shelf images (SKU-110K), three simulated robot passes per rack with camera offset and exposure drift, "
        "and 10% of frames deliberately degraded with motion blur or under-exposure. 1,350 frames, with a record of which were re-passes and which were degraded, so every "
        "decision below can be scored rather than asserted.")]
S += [P("<b>Three filters, in order.</b>")]
S += bullets(["<b>Quality gates.</b> Mean luminance for exposure, variance of the Laplacian for blur. Classical computer vision, milliseconds per frame, no model needed. "
              "Exposure is checked first, because a dark frame also scores as blurred and would otherwise be mislabelled.",
              "<b>Near-duplicate removal.</b> A CLIP ViT-B/32 embedding per frame, and a frame is dropped when its cosine similarity to an already-kept frame exceeds 0.965. "
              "Pixel differencing fails here: a 3% camera shift changes almost every pixel while the content is identical.",
              "<b>Diversity sampling.</b> Farthest-point sampling over the survivors, keeping 85%, so the set spans the distribution instead of over-representing common rack types."])
if FUNNEL.exists(): S += [Spacer(1, 4), Image(str(FUNNEL), width=140 * mm, height=73 * mm)]
S += [P("<b>What it cost and what it kept.</b> 1,350 frames in, 532 out: 61% fewer to label. 427 of 450 racks still represented, so coverage held at 95%. "
        "Of the frames I deliberately degraded, the quality gates caught 71%, and 81% of what they flagged was genuinely degraded. Embedding de-duplication removed 74% of the synthetic re-passes. "
        "Then the fair test: YOLOv8n fine-tuned on 150 curated frames against 150 random frames, both scored on 80 racks held out entirely. Curated 0.48 mAP50, random 0.43. "
        "Same labelling budget, better model.")]
S += [P("<b>A starting ontology for Storage Health.</b> The shapes matter more than the names: they decide what the model can learn and where the labelling time goes.")]
S += [table([["Class", "Shape", "Why this shape"]] + [
    ["Pallet in location", "3D cuboid", "Occupancy and overhang are geometric; cuboids on the LIDAR sweep tie presence to a WMS location rather than a 2D box"],
    ["Location label or placard", "bounding box", "The rack address links every detection to a WMS location; a decoded-string attribute supports OCR error analysis"],
    ["Damaged stock or wrapping breach", "bitmask", "Damage is irregular and partial; a mask plus a severity attribute suits an alert threshold better than a box"],
    ["Leaning pallet lean axis", "polyline", "Lean is an angle, not an area; annotating the load edge lets you regress deflection and set a compliance threshold"],
    ["Aisle obstruction", "polygon", "Handles stray pallets, cages and people blocking a pass, which their job ad names as an operational signal"],
    ["Scan condition", "frame tag", "Glare, motion blur, low light and film reflection explain most false negatives; tagging them lets you correlate failures with conditions"],
], [42 * mm, 24 * mm, 96 * mm])]
S += [Spacer(1, 5), P("<b>Where I am probably wrong.</b> The re-passes are simulated, so a real fleet will de-duplicate less: stock moves, lighting changes, people appear. "
                      "The blur threshold is dataset-specific and would need setting per site. The model comparison is small and directional, not a benchmark. "
                      "Those are three good reasons to run this on one week of real data from one site instead of arguing about my proxy.", SM)]

doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=21 * mm, rightMargin=21 * mm, topMargin=17 * mm, bottomMargin=16 * mm,
                        title="Encord Commercial Associate practical exercise", author="Qais Al-Azkawi")
doc.build(S)
print(OUT)
