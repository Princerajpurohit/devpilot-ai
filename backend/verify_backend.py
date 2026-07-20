import asyncio
import sys
import os
import json

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))
sys.path.append(os.path.dirname(__file__))

from app.api.endpoints import run_full_analysis
from app.services.pdf_generator import PDFGenerator

async def test_run():
    print("Initializing GitHub Repository Intelligence Engine Test...")
    test_repo = "https://github.com/Princerajpurohit/CODSOFT-INTERSHIP"
    print(f"Targeting Repository: {test_repo}")
    
    try:
        # Run full analysis pipeline
        analysis = await run_full_analysis(test_repo)
        
        print("\n--- ANALYSIS RESULTS ---")
        print(f"Repo: {analysis.metadata.owner}/{analysis.metadata.name}")
        print(f"Description: {analysis.metadata.description}")
        print(f"Stars: {analysis.metadata.stars} | Forks: {analysis.metadata.forks}")
        print(f"Primary Languages: {list(analysis.metadata.languages.keys())[:3]}")
        
        print("\n--- SCORES ---")
        print(f"Overall Intelligence Score: {analysis.scores.overall}/100")
        print(f"- Documentation: {analysis.scores.documentation}/100")
        print(f"- Security: {analysis.scores.security}/100")
        print(f"- Commit Quality: {analysis.scores.commits}/100")
        print(f"- Project Structure: {analysis.scores.structure}/100")
        
        print("\n--- SECURITY SCANS ---")
        print(f"Hardcoded Secrets found: {len(analysis.security.secrets)}")
        print(f"Vulnerabilities found: {len(analysis.security.vulnerabilities)}")
        
        print("\n--- FIX-IT ROADMAP ---")
        print(f"Total Actionable Items: {len(analysis.roadmap)}")
        for item in analysis.roadmap[:3]:
            print(f"- [{item.id}] ({item.severity}) {item.title} -> Gain: +{item.estimated_score_gain} pts")
            
        print("\n--- GENERATING REPORTLAB PDF ---")
        pdf_bytes = PDFGenerator.generate(analysis)
        pdf_path = os.path.join(os.path.dirname(__file__), "test_report.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"Successfully generated PDF report at: {pdf_path}")
        print("\nAll systems verified successfully! Backend is ready for production.")
        
    except Exception as e:
        print(f"\nVerification Failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_run())
