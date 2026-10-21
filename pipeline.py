from outliner import outline_create
from writter import writter
from editer import Editer
from analyzer import Analyzer
import json
from collections.abc import Callable
from json_hendler import Json_hendler


ProgressCallback = Callable[[str], None]


async def pipeline(topic, on_progress: ProgressCallback | None = None):

    print("\n" + "=" * 60)
    print("🚀 PIPELINE STARTED")
    print("=" * 60)
    print(f"[INPUT] Topic: {topic}")

    def report_progress(message: str) -> None:
        if on_progress is not None:
            on_progress(message)

    # =========================================================
    # OUTLINE
    # =========================================================
    print("\n[OUTLINE] Starting outline creation...")
    report_progress("Creating the article outline")

    outline = await outline_create(topic)

    print("[OUTLINE] Outline created successfully.")
    print(f"[OUTLINE] Type: {type(outline)}")
    print(f"[OUTLINE] Length: {len(outline)}")

    # ---------------- OUTLINE ANALYSIS ----------------
    print("\n[OUTLINE ANALYZER] Analyzing outline...")
    report_progress("Reviewing the outline")

    outline_analyzer = await Analyzer(outline)

    print("[OUTLINE ANALYZER] Raw response:")
    print(outline_analyzer)

    analysis = json.loads(outline_analyzer)
    # json_result = json.loads(outline_analyzer)
    # analysis = Json_hendler(json_result)

    print(f"[OUTLINE ANALYZER] Approved: {analysis['Approved']}")
    print(f"[OUTLINE ANALYZER] Feedback: {analysis.get('Feedback', '')}")

    # ---------------- OUTLINE RETRY LOOP ----------------
    outline_revision = 0
    while not analysis["Approved"]:
        outline_revision += 1

        print("\n[OUTLINE] ❌ Outline rejected.")
        print("[OUTLINE] 🔄 Creating improved outline...")
        report_progress(f"Revising the outline (attempt {outline_revision})")

        outline = await outline_create(analysis["Feedback"])

        print("[OUTLINE] Improved outline created.")

        print("[OUTLINE ANALYZER] Re-analyzing outline...")
        report_progress("Reviewing the revised outline")

        outline_analyzer = await Analyzer(outline)
        analysis = json.loads(outline_analyzer)
        # json_result = json.loads(outline_analyzer)
        # analysis = Json_hendler(json_result)

        print(f"[OUTLINE ANALYZER] Approved: {analysis['Approved']}")
        print(f"[OUTLINE ANALYZER] Feedback: {analysis.get('Feedback', '')}")

    print("\n[OUTLINE] ✅ Outline approved.")
    report_progress("Outline approved")

    # =========================================================
    # ARTICLE WRITING
    # =========================================================
    print("\n[WRITER] Starting article writing...")
    report_progress("Writing the first article draft")

    article = await writter(outline)

    print("[WRITER] Article written successfully.")
    print(f"[WRITER] Type: {type(article)}")
    print(f"[WRITER] Length: {len(article)}")

    # ---------------- ARTICLE ANALYSIS ----------------
    print("\n[ARTICLE ANALYZER] Analyzing article...")
    report_progress("Reviewing the article draft")

    article_analysis = await Analyzer(article)

    print("[ARTICLE ANALYZER] Raw response:")
    print(article_analysis)

    analysis = json.loads(article_analysis)

    print(f"[ARTICLE ANALYZER] Approved: {analysis['Approved']}")
    print(f"[ARTICLE ANALYZER] Feedback: {analysis.get('Feedback', '')}")

    # ---------------- ARTICLE RETRY LOOP ----------------
    article_revision = 0
    while not analysis["Approved"]:
        article_revision += 1

        print("\n[WRITER] ❌ Article rejected.")
        print("[WRITER] 🔄 Rewriting article using feedback...")
        report_progress(f"Rewriting the article (attempt {article_revision})")

        article = await writter(analysis["Feedback"])

        print("[WRITER] Improved article created.")

        print("[ARTICLE ANALYZER] Re-analyzing article...")
        report_progress("Reviewing the revised article")

        article_analysis = await Analyzer(article)
        analysis = json.loads(article_analysis)

        print(f"[ARTICLE ANALYZER] Approved: {analysis['Approved']}")
        print(f"[ARTICLE ANALYZER] Feedback: {analysis.get('Feedback', '')}")

    print("\n[WRITER] ✅ Article approved.")
    report_progress("Article approved")

    # =========================================================
    # EDITING
    # =========================================================
    print("\n[EDITOR] Starting final editing...")
    report_progress("Polishing and editing the approved article")

    final = await Editer(article)

    print("[EDITOR] Final version created.")
    print(f"[EDITOR] Type: {type(final)}")
    print(f"[EDITOR] Length: {len(final)}")

    # ---------------- FINAL ANALYSIS ----------------
    print("\n[FINAL ANALYZER] Analyzing edited article...")
    report_progress("Reviewing the polished article")

    final_analysis = await Analyzer(final)

    print("[FINAL ANALYZER] Raw response:")
    print(final_analysis)

    analysis = json.loads(final_analysis)

    print(f"[FINAL ANALYZER] Approved: {analysis['Approved']}")
    print(f"[FINAL ANALYZER] Feedback: {analysis.get('Feedback', '')}")

    # ---------------- FINAL RETRY LOOP ----------------
    final_revision = 0
    while not analysis["Approved"]:
        final_revision += 1

        print("\n[EDITOR] ❌ Final version rejected.")
        print("[EDITOR] 🔄 Editing again using feedback...")
        report_progress(f"Polishing the article again (attempt {final_revision})")

        final = await Editer(analysis["Feedback"])

        print("[EDITOR] Improved final version created.")

        print("[FINAL ANALYZER] Re-analyzing final version...")
        report_progress("Reviewing the updated polished article")

        final_analysis = await Analyzer(final)
        analysis = json.loads(final_analysis)

        print(f"[FINAL ANALYZER] Approved: {analysis['Approved']}")
        print(f"[FINAL ANALYZER] Feedback: {analysis.get('Feedback', '')}")

    print("\n[EDITOR] ✅ Final version approved.")
    report_progress("Final article approved")

    # =========================================================
    # FINAL RETURN
    # =========================================================
    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)
    report_progress("Article generation complete")

    return final
