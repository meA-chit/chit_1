# Kids module: focused research on three open questions

- Date: 2026-10-07
- Status: **Directional.** Desk research only. It follows up the gaps listed at the end of the kids breakdown given in chat, and refines [`03-missing-feature-analysis.md`](03-missing-feature-analysis.md).
- Questions: (1) How do German school portals work, and what can Chit connect to? (2) Is there demand for grade tracking and medication reminders? (3) Will 10–13-year-olds use a parent-paired app?

## Evidence quality

| Question | Evidence found | Quality |
|---|---|---|
| 1. School portals | Vendor pages and comparison sites; WebUntis help pages; a 2016 Bitkom survey; data-protection commentary on WhatsApp | **Weak for parent experience**, adequate for what each product exposes technically. No parent forum or review data surfaced. |
| 2a. Grades | Commentary and anecdotes about US parent portals; expert advice quoted in news pieces | **Weak.** No demand data, no controlled study. |
| 2b. Medication | A randomised trial (asthma reminders), small feasibility studies, app reviews | **Medium** for reminders working; **weak** for ADHD and for family apps specifically. |
| 3. Child use | KIM 2024 (Germany, n=1,225, parent-reported), Oxford and UCF studies on teen reaction to monitoring | **Good** for ownership and rules, **none** for what 10–13-year-olds want from a kid app. |

## 1. German school portals and what Chit can connect to

**What exists.** Schools choose the platform, not parents. The names that recur are Sdui (parent letters with reply, push notifications, substitution plan), Schulmanager Online (digital class book, absences, timetable, letters), schul.cloud (messenger with calendar and files) and Sharezone (a student-and-class planner with a shared homework diary, timetable, grades and info notes). Parents see different functions depending on the school and the package. [S1][S2]

**What parents experience.** Direct parent complaints were not found. What the sources do show:
- WhatsApp is widely used between teachers and parents and is a data-protection grey zone. Rules differ by state; Austria bans it in schools, and a Thuringia dispute led the regulator to say it does not belong in schools. [S3]
- A 2016 Bitkom survey found 34% of parents said teachers use no electronic communication and 22% got school news only on paper. It is old, so treat it as a floor on how analogue some schools are. A 2024 Bitkom survey of parents (n=273) rated digital technology in lessons 3.3 on a school-grade scale. [S4]
- One teacher-forum comment cites "lack of overview" in WhatsApp and SchoolFox groups. It is a single opinion. [S3]

**What can be connected.**
| Source | Route | Verdict |
|---|---|---|
| **WebUntis** timetable | Official personal **iCal subscription link**, available to teachers and students, not administrators; the school must order the feature; updates can lag; Untis notes hosting fees may rise for student subscriptions [S5] | **Works with Chit's existing calendar links** (household setup), provided the feed lists each date; series need the recurrence fix (gap 4). Whether *parents* can get a link is unconfirmed. |
| **Schulmanager Online** | No official export found; only unofficial API projects [S5] | **Do not build on it.** Unofficial interfaces can break without notice and may breach terms (my assessment, not from the sources). |
| **LOGINEO NRW** | CalDAV offered, per an authority reply [S5] | Possible later, state-specific. |
| **Sdui, schul.cloud** | No parent-side data export found | Not connectable from what I found. |
| **Parent letters and PDFs** | Arrive by email, in apps, or on paper | Needs capture (Smart Import), not an integration. |

**What is already built.** Household setup lets a parent attach a calendar link to each child's school, care or sport calendar and assign it to members (the product owner confirmed this is how school events and regular trainings reach the family view). So the cheap first step for timetables, a link import, exists. What it lacks is recurrence: the reader ignores `RRULE`, so a series published as one repeating event is not expanded. Regular activities are also weekly-only, and there is no in-app way to create a one-off or recurring event (see [`03-missing-feature-analysis.md`](03-missing-feature-analysis.md), section 3).

**Implication for "automatic capture" (M2, M14).**
1. Fix recurrence in the feed reader (M1) so the existing links work for series, and check the real school and club feeds for `RRULE`.
2. What links cannot carry is parent letters, trip notices and one-off announcements. The general solution is capture from what parents already receive (forwarded email, PDF, photo of a paper letter), not portal-by-portal integrations. There are too many platforms and schools, not parents, choose them.
3. Local-first handling matters here: the sources show strong data-protection sensitivity about school communication. That supports a local-processing story and raises the bar for any cloud model.
4. **Cheapest next test:** ask five German parents which platform their school uses, whether they can get a calendar link, and how they receive letters. That decides how much of M2 is feeds versus capture.

## 2a. Grades: demand is unproven and the main risk is harm from over-checking

- No source showed demand for a standalone grade-tracking app. The existing alternative in the US is the school's parent portal (PowerSchool, Infinite Campus, Schoology). [S6]
- Commentary on those portals is consistent: real-time grades lead to "hyperchecking" (one review cites about eight checks a day; a teacher reports parents checking five or six times a day), higher student stress, and panic when a portal is incomplete and shows a "failing" grade because work has not been entered yet. [S6]
- Advice quoted from a Harvard education researcher is to check about weekly and avoid overbearing monitoring that undermines the child's autonomy. [S6]
- The product responses already in the market are **digests and thresholds**: Schoology offers a daily or weekly digest, and Aeries and some districts offer alerts when a grade crosses a threshold. [S6]

**What this means for Chit's grades feature**
- It matches two good practices: grades are parent-only and never in the child's view, and an average never treats a missing grade as zero. The second directly addresses the "incomplete portal causes panic" complaint.
- It misses one: there is no digest. A **weekly summary** (new grades, trend, nothing else) is the better default than a live dashboard.
- Because entry is manual, value depends on the parent typing grades. In Germany I did not find evidence of a parent-facing grade portal, so a manual log may still be useful, but that is a **hypothesis to test**, not a finding.
- Confidence: low. Do not invest further until five to eight parents say they would use it.

## 2b. Medication: reminders work, and that is exactly what is not built

- The strongest evidence is for **reminders and refill prompts**. A randomised trial of about 1,200 children aged 3–12 with asthma (Kaiser Permanente, published in JAMA Pediatrics) reported higher adherence to inhaled steroids over 24 months when parents got automated refill calls. [S7]
- Engagement is the weak point. In a Vanderbilt trial, 87% signed in but only about half showed any activity. [S7]
- Parents are typically the ones managing a child's medication. A small qualitative study (8 children, 10 parents) found children have limited involvement and like rewards and child-friendly design. [S7]
- ADHD-specific evidence is thin (feasibility studies only). [S7]
- Competing apps: Medisafe has a "Medfriend" who is alerted when a dose is missed, reminders that keep alerting until confirmed, refill reminders, multiple profiles and PDF sharing; complaints are about editing bugs and duplicate or late reminders; premium is about $4.99 a month (sources disagree). MyTherapy is free, with barcode entry and stock counting. German tools can import the national medication plan by QR code. [S8][S9]

**What this means for Chit's medication feature**
| Evidence-backed need | Chit today |
|---|---|
| Reminder at the dose time, persistent until confirmed | **Not built** (needs push; kids README says so) |
| Another adult is told when a dose is missed | Not built; the log has "given" and "missed" and a reminded adult is stored |
| Refill warning | Built (at 10 days or less of supply) |
| Easy entry (barcode, QR plan import) | Not built; all manual |
| Strict privacy, no cloud, off shared screens | **Built** (a real differentiator) |

Chit's medication feature is currently a **log with a refill warning**, not a reminder. The category already has free, polished apps, so a stand-alone medication app is not a wedge. Its value is being inside the family hub with strict privacy. Either build dose-time reminders with a missed-dose alert to a second adult (the evidence-supported core), or leave it parked. Confidence: medium on the need, low on whether families would use Chit over a free dedicated app.

## 3. Will 10–13-year-olds use a parent-paired app?

**Ownership (KIM 2024, Germany, parent-reported, n=1,225)** [S10]
| Age | Own smartphone |
|---|---|
| 6–7 | 11% |
| 8–9 | 33% |
| 10–11 | **63%** |
| 12–13 | **79%** |

- The jump of 30 points between 8–9 and 10–11 coincides with the move to secondary school.
- Of children with a smartphone, 82% take it to school and two thirds to sport or youth group. Reasons given for no own phone: age (68%), "does not need one" (43%).
- Parents' behaviour: 40% of children with their own phone have child-protection settings on; 71% of parents whose children use online services set no safety settings on any device; 52% bar the phone from the room during homework.
- Parents without a phone for their child said location (83%) and age-adjustable settings (79%) matter most when buying one.

**What it means for Chit**
- The ADR-0012 assumption (10+) **fits the data**: most 10–11s and about four fifths of 12–13s have a phone.
- A third of 10–11-year-olds do not. A **shared family tablet** or a parent-lent phone needs to be a supported pairing target; today the design assumes the child's own phone.
- **The homework-phone rule is a design tension.** Half of parents ban the phone during homework. The homework tab should be a place to *plan and check off*, not a tool you have to hold while working. Worth asking parents whether it conflicts with their rules.
- Parents already value location. Chit deliberately has none; that stays a conscious choice (it conflicts with the privacy principle), but expect parents to ask.

**How teens react to parental apps** [S11]
- Oxford focus groups (UK, ages 16–17, seven groups) found acceptance depends on how the app is introduced and whether the teen's autonomy is respected. Location sharing was accepted more than content monitoring, and more again when reciprocal.
- A University of Central Florida study (215 US parent-teen pairs, 2018, self-reported) linked parental-control app use with more, not fewer, online risks, and about 79% of reviews written by children rated these apps two stars or less.
- Both concern **monitoring and restriction apps**. Chit's kid app is closer to a planner the child benefits from (own school day, homework, stars), but it is still parent-controlled, so the teen-trust findings apply to how it is introduced.

**No evidence was found** on what 10–13-year-olds actually want from a kid-facing app. Greenlight's published praise comes from parents and company copy, and its child experience is deliberately limited. So engagement by children is **unvalidated**.

**Design implications (cheap to adopt)**
1. Extend the kid app's "About me" sheet, which already lists which sections the parents share, to cover what the parents see of the child's own activity. Transparency is the strongest lever in the research for acceptance. (Design: `docs/modules/kids/kid-experience.md`, section 4.)
2. Keep it free of monitoring: no location, no content or usage tracking. State this on the pairing screen.
3. Let the child do something useful that is theirs alone: add homework (built), see the school day (built), and consider their own reminder times.
4. Support pairing on a shared device.
5. **Cheapest test:** put the app in front of five to eight children aged 10–13 in a 20-minute session. Ask what they would open it for, what they would hide, and what annoys them.

## Updated priorities for the kids module

| Priority | Change from the earlier breakdown | Why |
|---|---|---|
| Changed | **Calendar-link import already exists** (per child, in household setup); what is needed is feed recurrence (`RRULE`) and non-weekly activities | The owner confirmed links carry school and sport events; recurrence is the gap. |
| Up | **Transparency screen and shared-device pairing** in the kid app | Backed by the strongest evidence on teen acceptance and KIM data. |
| Same | **Smart Import** for parent letters and PDFs | Still the largest gap; it is the general solution because portals are too many. |
| Changed | **Grades: weekly digest instead of live view; validate before investing** | Evidence points to harm from over-checking and none for demand. |
| Changed | **Medication: either build dose-time reminders plus a missed-dose alert to a second adult, or park it** | Reminders are the evidence-backed part and are unbuilt; the category has free competitors. |
| Dropped | **Direct integrations with Schulmanager, Sdui, schul.cloud** | No official export; unofficial APIs are fragile. |
| Unchanged | No location sharing; no real-money allowance | Conflicts with principles; regulated. |

## Open questions that research could not answer
- Which school platforms do the target German households' schools use, and do parents get calendar links? Do your own school and sport feeds contain `RRULE`? (Open the feeds as text; five parent conversations.)
- Do parents want grade entry at all, and how often would they look? (Five to eight interviews.)
- What do 10–13-year-olds want from this app? (Five to eight child sessions.)
- Is a standalone medication feature wanted if free dedicated apps exist? (Ask the same parents.)

## Sources
| ID | Source |
|---|---|
| S1 | [Sdui](https://sdui.de/schule-online/), [Schulmanager Online (App Store)](https://apps.apple.com/de/app/schulmanager-online/id1451616735) |
| S2 | [School messenger comparison](https://lernmarktplatz.de/pages/kommunikation-mit-schuelern-eltern-dsgvo-konforme-schulmessenger-im-vergleich), [Sharezone (App Store)](https://apps.apple.com/DE/app/id1434868489) |
| S3 | [WhatsApp between teachers and parents is a grey zone](https://www.abendzeitung-muenchen.de/panorama/whatsapp-zwischen-lehrern-und-eltern-ist-grauzone-art-631068), [Data-protection criticism of teachers using WhatsApp](https://www.news4teachers.de/2019/06/datenchuetzer-kritisiert-lehrer-harsch-dafuer-whatsapp-zu-nutzen-unterbelichtet/), [Sdui as a WhatsApp alternative](https://www.news4teachers.de/2019/10/eine-fuer-alles-schul-app-sdui-ueberzeugt-als-sichere-whatsapp-alternative/) |
| S4 | [Bitkom: teachers swear by paper (2016)](https://www.bitkom.org/Presse/Presseinformation/Lehrer-schwoeren-auf-Papier), [Bitkom: parents give schools a 4 on digitalisation](https://www.bitkom.org/Presse/Presseinformation/Note-4-Eltern-geben-Schulen-kein-gutes-Digitalzeugnis) |
| S5 | [WebUntis calendar subscription (Untis help)](https://webhelp.untis.at/HTML/WebHelp/uk/untis/wu_ical_kalender_abonnement.htm), [WebUntis calendar sheet (school PDF)](https://www.gymnasiumkerpen.eu/medien/download-center/digitalisierung/webuntis_info_kalender.pdf), [NRW ministry on calendar sync](https://www.schulministerium.nrw/node/26413), [Unofficial Schulmanager API projects](https://gitblind.noratr.app/topics/schulmanager) |
| S6 | [Reason: the pupil panopticon](https://reason.com/2024/04/30/the-pupil-panopticon/), [Hyperchecking grades (Fronteras)](https://fronterasdesk.org/content/1868452/some-students-and-parents-are-hyperchecking-grades-why-could-be-problem), [KQED MindShift: how closely should parents track grades](https://www.kqed.org/mindshift/31237/good-read-how-closely-should-parents-track-their-kids-grades) |
| S7 | [MyMediHealth (AHRQ)](https://digital.ahrq.gov/ahrq-funded-projects/my-medihealth-paradigm-children-centered-medication-management), [Paediatric medication adherence apps, child and parent views](https://scholars.uky.edu/en/publications/paediatric-use-of-medications-and-adherence-apps-a-qualitative-an/), [Phone reminders for paediatric asthma](https://www.hcplive.com/view/adherence-for-pediatric-asthma-medication-improved-with-phone-call-reminders), [TAICAM trial protocol](https://cdn.clinicaltrials.gov/large-docs/10/NCT03907410/Prot_SAP_000.pdf) |
| S8 | [Medication reminder apps comparison](https://caringvillage.com/blog/caregiver-tech/medication-reminder-apps/), [Medisafe overview](https://intuitionlabs.ai/software/patient-education-engagement/medication-adherence-apps/medisafe) |
| S9 | [Smartphone as medication plan (PTA heute)](https://www.ptaheute.de/aktuelles/2019/12/05/wie-das-smartphone-zum-medikationsplan-wird), [Cincinnati Children's on medication apps](https://www.cincinnatichildrens.org/professional/resources/staff-bulletin/archives/2018/january/medication-manager-apps) |
| S10 | [KIM-Studie 2024 (mpfs, PDF)](https://www.pit.sachsen.de/download/KIM-Studie-2024.pdf), pages 7–9, 21, 70, 80–81 |
| S11 | [Oxford Internet Institute on parental control technologies](https://www.oii.ox.ac.uk/news-events/videos/the-role-and-impact-of-parental-control-technologies-in-parent-teen-relationships/), [UCF on parental control apps](https://www.ucf.edu/news/apps-keep-children-safe-online-may-counterproductive/), [Beyond parental control (arXiv 2025)](https://arxiv.org/pdf/2503.22995), [The monitored generation (Nuffield)](https://www.nuffieldfoundation.org/wp-content/uploads/2025/11/The-monitored-generation.pdf) |
