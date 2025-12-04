import os
import csv
import glob
import json
import hashlib
import requests
import logging
from difflib import SequenceMatcher
from pdfminer.high_level import extract_text

logging.getLogger("pdfminer").setLevel(logging.ERROR)

PDF_URLS = PDF_URLS = [
    "https://www.dni.gov/files/NCTC/documents/features_documents/Intelligence_Guide_for_First_Responders.pdf",
    "https://govinfo.library.unt.edu/wmd/report/chapter7_fm.pdf",
    "https://safeandfree.io/wp-content/uploads/2023/11/USA_Surveillance_Final.pdf",
    "https://apps.dtic.mil/sti/tr/pdf/ADA585920.pdf",
    "https://www.govinfo.gov/content/pkg/COMPS-1493/pdf/COMPS-1493.pdf",
    "https://api.pageplace.de/preview/DT0400.9780429962875_A37405800/preview-9780429962875_A37405800.pdf",
    "https://keystone.ndu.edu/Portals/86/10_%20SOF%20Interagency%20Reference%20Guide.pdf",
    "https://www.justice.gov/archive/olp/pdf/intelligence_reform_and_terrorism_prevention_act.pdf",
    "https://www.fbi.gov/file-repository/final-9-11-review-commission-report-unclassified.pdf",
    "https://www.rand.org/content/dam/rand/pubs/research_reports/RRA1200/RRA1245-1/RAND_RRA1245-1.pdf",
    "https://www.sipa.columbia.edu/sites/default/files/migrated/migrated/documents/FOR%2520PUBLICATION%2520_TheMarkleFoundation.pdf",
    "https://www.governmentattic.org/13docs/NROtownHallWebPages_2002-2008U.pdf",
    "https://www.congress.gov/crs_external_products/R/PDF/R45720/R45720.2.pdf",
    "https://www.cia.gov/resources/csi/static/The-Agency-and-Hill.pdf",
    "https://ia601200.us.archive.org/24/items/SpiesWiretapsAndSecretOperations/Spies%2CWiretaps%20and%20Secret%20Operations.pdf",
    "https://jsouapplicationstorage.blob.core.windows.net/press/270/2011SOFIACTRefManual_final.pdf",
    "https://upload.wikimedia.org/wikipedia/commons/2/29/RL32508_%28IA_RL32508-crs%29.pdf",
    "https://www.dhs.gov/sites/default/files/2024-04/2024_0311_fy_2025_budget_in_brief.pdf",
    "https://columbialawreview.org/wp-content/uploads/2016/04/Casey-Kevin.pdf",
    "https://henryjacksonsociety.org/wp-content/uploads/2015/05/Surveillance-after-Snowden.pdf",
    "https://www.everycrsreport.com/files/20120918_R40240_624b497550c0a7136208b6e22ece2edc0d83c0f5.pdf",
    "http://research.unl.edu/events/docs/Intelligence%20Analysis%20Behavioral%20and%20Social%20Scientific%20Foundations%20NRC%202011.pdf",
    "https://www.intelligence.senate.gov/wp-content/uploads/2024/08/sites-default-filesations-crpt-118srpt181.pdf",
    "https://dcips.defense.gov/Portals/50/Documents/Training_Docs/HR%20Elements%20for%20HR%20Practitioners/Participant%20Guide/HRP-RefGuide_Feb2017.pdf",
    "https://ccrjustice.org/sites/default/files/assets/2008-05-06%20Mem%20in%20Support%20of%20Mot%20for%20Summ%20Judgmnt%20-%20McConnell%20Affidavit%20(corrected).pdf",
    "https://trepo.tuni.fi/bitstream/10024/143088/2/OksanenJarkko.pdf",
    "https://oversight.house.gov/wp-content/uploads/2024/10/CCP-Report-10.24.24.pdf",
    "https://cyberwar.nl/d/20150200_Business-Executives-for-NatSec_BENS_Domestic-Security-Report_Feb2015.pdf",
    "https://static.heritage.org/project2025/2025_MandateForLeadership_FULL.pdf",
    "https://www.marines.mil/Portals/1/Publications/MCRP%202-10A.1%20(SECURED).pdf?ver=eMRBwMdOdqN2bMGFMCnxTQ%3D%3D",
    "https://www.esd.whs.mil/portals/54/documents/dd/issuances/dodd/524001p.pdf",
    "https://www.govinfo.gov/content/pkg/GPO-WMD/pdf/GPO-WMD-1-17.pdf",
    "https://dsb.cto.mil/wp-content/uploads/reports/2010s/ADA543575.pdf",
    "https://www.jcs.mil/portals/36/documents/library/instructions/cjcsi%205123.01i.pdf",
    "https://law.stanford.edu/wp-content/uploads/2018/03/young-1.pdf",
    "https://comptroller.war.gov/Portals/45/documents/defbudget/fy2013/budget_justification/pdfs/03_RDT_and_E/United_States_Special_Operations_Command_PB_2013-1.pdf",
    "https://www.nomos-elibrary.de/10.5771/9780810874763-185.pdf",
    "https://www.cia.gov/resources/csi/static/159886efc8ff17ac93a5ffc027d9a6a0/dci_leaders.pdf",
    "https://www.hoover.org/sites/default/files/research/docs/8-Boskin_DefenseBudgeting_ch3.pdf",
    "https://www.governmentattic.org/24docs/NROboozAHContracts_2009-2013.pdf",
    "https://apps.dtic.mil/sti/tr/pdf/ADA552990.pdf",
    "https://jsouapplicationstorage.blob.core.windows.net/press/230/2013SOFIACTRefManual_Final.pdf",
    "https://www.jcs.mil/Portals/36/Documents/Library/Instructions/CJCSI%201001.01C.pdf",
    "https://www.dni.gov/files/documents/CLPO/ICOTR_Transparency_Tracker_sorted_by_date_posted.pdf",
    "https://epic.org/wp-content/uploads/foia/nara/kavanaugh/EPIC-18-08-01-NARA-FOIA-20190729-Production-Staff-Secretary-Keyword-NSA-pt3.pdf",
    "https://www.congress.gov/117/plaws/publ328/PLAW-117publ328.pdf",# (TODO: DON'T SKIP THIS FILE)
    "https://d34w7g4gy10iej.cloudfront.net/pubs/pdf_69517.pdf",
    "https://www.openthegovernment.org/sites/default/files/otg/SRC2007.pdf",
    "https://app7.legco.gov.hk/rpdb/en/file.aspx?id=fa5817f7198c415eb0b94860a4f4d975&type=pdf&lang1=en&lang2=en",
    "https://www.ikn.army.mil/apps/MIPBW/MIPB_Issues/MIPBJul_Sep17IKNmod.pdf",
    "https://www.marines.mil/Portals/1/Publications/MCWP%202-1%20Intelligence%20Operations.pdf",
    "https://2009-2017.state.gov/documents/organization/150085.pdf",
    "https://irp.fas.org/doddir/army/tc2-19-01.pdf",
    "https://media.defense.gov/2017/Jun/19/2001765010/-1/-1/0/AP_2014-1_BROWN_STRATEGY_INTELLIGENCE_SURVEILLANCE_RECCONNAISSANCE.PDF",
    "https://www.ikn.army.mil/apps/MIPBW/MIPB_Features/BuildingCollectionManagersforTodaysMultiDomainBattlefiled-Cordes.pdf",
    "https://info.publicintelligence.net/USArmy-GeospatialIntel.pdf",
    "https://www.rand.org/content/dam/rand/pubs/technical_reports/2008/RAND_TR459.pdf",
    "https://apps.dtic.mil/sti/pdfs/AD1128558.pdf",
    "https://www.bits.de/NRANEU/others/amd-us-archive/fm2-0(04).pdf",
    "https://www.ojp.gov/pdffiles1/Photocopy/134434NCJRS.pdf",
    "https://nsarchive.gwu.edu/sites/default/files/documents/3678217/Document-11-Department-of-the-Army-FM-3-12.pdf",
    "https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodm/520507m1.PDF?ver=o_3_m4lDAtLKPOLQHatcYA%3D%3D",
    "https://www.dni.gov/files/ODNI/documents/21-113_MASINT_Primer__2022.pdf",
    "https://www.marines.mil/Portals/1/Publications/FM%202-22.3%20%20Human%20Intelligence%20Collector%20Operations_1.pdf",
    "https://edocs.nps.edu/2012/December/joint%20pub%202_03.pdf",
    "https://info.publicintelligence.net/CALL-CommandersGuideHUMINT.pdf",
    "https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-30r1.pdf",
    "https://www.nro.gov/Portals/65/documents/foia/docs/HOSR/SC-2017-00006l.pdf",
    "https://apps.dtic.mil/sti/tr/pdf/ADA555809.pdf",
    "https://ndupress.ndu.edu/Portals/68/Documents/jfq/jfq-72/jfq-72_39-46_Brown.pdf",
    "https://www.globalsecurity.org/military/library/policy/usaf/afdd/2-0/afdd2-0.pdf",
    "https://www.fema.gov/sites/default/files/documents/fema_rd_response-recovery-fiop-npb-042025.pdf",
    "https://upload.wikimedia.org/wikipedia/commons/2/28/Crowdsourcing_ISR-_a_systems_thinking_approach_to_knowledge_dynamics_in_intelligence_operations_through_application_of_collaborative_filters_%28IA_crowdsourcingisr1094537638%29.pdf",
    "https://api.army.mil/e2/c/downloads/2025/05/06/fdd320b3/no-25-987-multi-domain-operations-range-guide-for-company-grade-through-field-grade-leaders-apr-25.pdf",
    "https://www.bits.de/NRANEU/others/amd-us-archive/FM34-60%2895%29.pdf",
    "https://www.archives.gov/files/declassification/iscap/pdf/2014-004-doc01.pdf",
    "https://www.jcs.mil/Portals/36/Documents/Doctrine/training/jts/cjcsi_3162_02.pdf?ver=2019-03-13-092459-350",
    "https://www.airuniversity.af.edu/Portals/10/ASPJ/journals/Volume-26_Issue-6/ASPJ-Nov-Dec-2012.pdf",
    "https://sgtsdesk.com/wp-content/uploads/2019/01/AR-350-1-DEC2017.pdf",
    "https://cioms.ch/wp-content/uploads/2022/05/CIOMS-WG-XIV_Draft-report-for-Public-Consultation_1May2025.pdf",
    "https://www.dau.edu/sites/default/files/2024-01/Manual%20-%20JCIDS%20Oct%202021.pdf",
    "https://nmio.ise.gov/Portals/16/National%20MDA%20Plan%202023%20%28U%29.pdf",
    "https://www.dote.osd.mil/Portals/97/pub/reports/FY2020/other/2020DOTEAnnualReport.pdf",
    "https://www.rand.org/content/dam/rand/pubs/research_reports/RR4300/RR4360/RAND_RR4360.pdf",
    "https://unidir.org/wp-content/uploads/2023/05/Science-and-Technology-for-Monitoring-and-Investigation-of-WMD-Compliance.pdf",
    "https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/311517p.pdf",
    "https://www.intelligence.senate.gov/wp-content/uploads/2024/08/sites-default-files-commission-report.pdf",
    "https://www.dhs.gov/sites/default/files/publications/I%26A%20PTO%20Records.pdf",
    "https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodd/510521p.pdf",
    "https://ndupress.ndu.edu/Portals/68/Documents/jfq/jfq-94/jfq-94_18-25_Kwoun.pdf?ver=2019-07-25-162024-707"
]

JSON_DIR = "../tmp_pdfs"
CACHE_DIR = "./cached_pdfs"
os.makedirs(CACHE_DIR, exist_ok=True)

OUTPUT_CSV = "json_pdf_matches.csv"
SIMILARITY_THRESHOLD = 0.20


# 🔹 Hash URL → stable local filename
def _hashed_filename(url: str) -> str:
    digest = hashlib.sha256(url.encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{digest}.pdf")

import random
from requests.adapters import HTTPAdapter, Retry

# Multiple real browser User-Agents for rotation
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36 Edg/122.0",
]

DEFAULT_HEADERS = {
    "Accept": "application/pdf,application/octet-stream,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

def get_cached_pdf(url: str) -> str | None:
    filename = _hashed_filename(url)

    # Return cached version if already downloaded
    if os.path.exists(filename):
        print(f"📁 Cache hit: {url}")
        return filename

    session = requests.Session()

    # Robust retry strategy
    retries = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1,
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))

    # Randomize headers per attempt
    headers = DEFAULT_HEADERS.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)

    print(f"⬇️ Downloading with spoofed headers: {url}")
    try:
        r = session.get(url, headers=headers, stream=True, timeout=60)
        r.raise_for_status()

        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=2048):
                if chunk:
                    f.write(chunk)

        return filename

    except Exception as e:
        print(f"❌ Download failed: {url} — {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return None


# 🔹 Compare substring first → fallback to fuzzy
def score_context_against_pdf(context: str, pdf_text: str) -> float:
    if not context or not pdf_text:
        return 0.0

    if context in pdf_text:
        return 1.0

    return SequenceMatcher(None, context, pdf_text).ratio()


# 🔹 Extract text from PDF safely
def extract_pdf_text(path: str) -> str:
    try:
        return extract_text(path) or ""
    except Exception:
        return ""


# 🔹 MAIN matching logic for one JSON file
def match_json_to_pdf(json_file: str):
    with open(json_file, "r") as f:
        try:
            entries = json.load(f)
        except Exception:
            entries = []

    if not entries:
        return ("NONE", 0.0, "EMPTY JSON")

    contexts = [e.get("context", "") for e in entries if e.get("context")]
    if not contexts:
        return ("NONE", 0.0, "NO CONTEXT")

    best_url = "NONE"
    best_score = 0.0

    print(f"🧠 Evaluating {len(contexts)} context blocks")

    for url in PDF_URLS:
        print(f"🔎 Testing against: {url}")

        pdf_path = get_cached_pdf(url)
        if not pdf_path:
            continue

        pdf_text = extract_pdf_text(pdf_path)
        if not pdf_text:
            print("⚠ No readable text extracted — skipping")
            continue

        # 🔍 Score each context independently
        for ctx in contexts:
            score = score_context_against_pdf(ctx, pdf_text)
            if score > best_score:
                best_score = score
                best_url = url

    if best_score < SIMILARITY_THRESHOLD:
        return ("NONE", best_score, "UNMATCHED")

    return (best_url, best_score, "MATCHED")


def main():
    json_files = glob.glob(os.path.join(JSON_DIR, "*_extracted.json"))
    print(f"📄 Found {len(json_files)} JSON files to match\n")

    results = []

    for jf in json_files:
        print(f"\n=== Processing: {os.path.basename(jf)} ===")
        matched_url, score, status = match_json_to_pdf(jf)
        results.append([
            os.path.basename(jf),
            matched_url,
            f"{score:.4f}",
            status
        ])

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["json_file", "matched_pdf_url", "match_score", "status"])
        writer.writerows(results)

    print("\n🎯 DONE — Results written to", OUTPUT_CSV)
    print("📁 Cached PDFs stored in:", CACHE_DIR)


if __name__ == "__main__":
    main()