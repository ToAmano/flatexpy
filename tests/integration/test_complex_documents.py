"""Integration tests for complex document structures."""

import os
import tempfile

from flatexpy.flatexpy_core import LatexExpandConfig, LatexExpander


class TestComplexDocuments:
    """Integration tests for complex document structures."""

    def test_document_with_packages_and_includes(self) -> None:
        """Test complex document with packages, graphics, and multiple includes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create complex main document
                main_content = (
                    "\\documentclass[12pt]{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\usepackage{amsmath}\n"
                    "\\graphicspath{{figures/}}\n"
                    "\\title{Complex Document}\n"
                    "\\author{Test Author}\n"
                    "\\begin{document}\n"
                    "\\maketitle\n"
                    "\\input{abstract}\n"
                    "\\input{introduction}\n"
                    "\\input{methods}\n"
                    "\\input{results}\n"
                    "\\input{conclusion}\n"
                    "\\end{document}\n"
                )

                # Create directory structure
                os.makedirs("figures")

                # Create included files
                files_content = {
                    "abstract.tex": (
                        "\\begin{abstract}\n"
                        "This is the abstract.\n"
                        "\\end{abstract}\n"
                    ),
                    "introduction.tex": (
                        "\\section{Introduction}\n"
                        "Introduction text with figure:\n"
                        "\\includegraphics{intro_fig}\n"
                    ),
                    "methods.tex": (
                        "\\section{Methods}\n"
                        "Methods description.\n"
                        "\\input{detailed_methods}\n"
                    ),
                    "detailed_methods.tex": (
                        "\\subsection{Detailed Methods}\n" "Detailed methodology.\n"
                    ),
                    "results.tex": (
                        "\\section{Results}\n"
                        "Results with equation:\n"
                        "\\begin{equation}\n"
                        "E = mc^2\n"
                        "\\end{equation}\n"
                        "And figure:\n"
                        "\\includegraphics{results_fig}\n"
                    ),
                    "conclusion.tex": ("\\section{Conclusion}\n" "Final thoughts.\n"),
                }

                # Create image files
                images = ["intro_fig.png", "results_fig.jpg"]
                for img in images:
                    with open(f"figures/{img}", "wb") as f:
                        f.write(f"fake {img} data".encode())

                # Write all files
                with open("main.tex", "w") as f:
                    f.write(main_content)

                for filename, content in files_content.items():
                    with open(filename, "w") as f:
                        f.write(content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all sections are included
                assert "\\begin{abstract}" in result
                assert "\\section{Introduction}" in result
                assert "\\section{Methods}" in result
                assert "\\subsection{Detailed Methods}" in result
                assert "\\section{Results}" in result
                assert "\\section{Conclusion}" in result

                # Verify graphics are processed
                assert "\\includegraphics{intro_fig.png}" in result
                assert "\\includegraphics{results_fig.jpg}" in result

                # Verify image files are copied
                assert os.path.exists("output/intro_fig.png")
                assert os.path.exists("output/results_fig.jpg")

                # Verify include markers are present
                assert ">>> input{abstract} >>>" in result
                assert ">>> input{detailed_methods} >>>" in result

            finally:
                os.chdir(original_cwd)

    def test_document_with_subdirectories(self) -> None:
        """Test document with includes from subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directory structure
                os.makedirs("chapters")
                os.makedirs("appendices")

                # Create main document
                main_content = (
                    "\\documentclass{book}\n"
                    "\\begin{document}\n"
                    "\\input{chapters/chapter1}\n"
                    "\\input{chapters/chapter2}\n"
                    "\\input{appendices/appendix_a}\n"
                    "\\end{document}\n"
                )

                # Create chapter files
                chapter1_content = "\\chapter{First Chapter}\n" "Chapter 1 content.\n"

                chapter2_content = "\\chapter{Second Chapter}\n" "Chapter 2 content.\n"

                appendix_content = (
                    "\\appendix\n" "\\chapter{Appendix A}\n" "Appendix content.\n"
                )

                # Write all files
                with open("main.tex", "w") as f:
                    f.write(main_content)

                with open("chapters/chapter1.tex", "w") as f:
                    f.write(chapter1_content)

                with open("chapters/chapter2.tex", "w") as f:
                    f.write(chapter2_content)

                with open("appendices/appendix_a.tex", "w") as f:
                    f.write(appendix_content)

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all content is included
                assert "\\chapter{First Chapter}" in result
                assert "\\chapter{Second Chapter}" in result
                assert "\\chapter{Appendix A}" in result
                assert "Chapter 1 content." in result
                assert "Chapter 2 content." in result
                assert "Appendix content." in result

                # Verify include markers with paths
                assert ">>> input{chapters/chapter1} >>>" in result
                assert ">>> input{chapters/chapter2} >>>" in result
                assert ">>> input{appendices/appendix_a} >>>" in result

            finally:
                os.chdir(original_cwd)

    def test_academic_paper_structure(self) -> None:
        """Test realistic academic paper structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create realistic academic paper structure
                os.makedirs("sections")
                os.makedirs("figures")
                os.makedirs("tables")

                # Main document
                main_content = (
                    "\\documentclass[11pt,letterpaper]{article}\n"
                    "\\usepackage{graphicx}\n"
                    "\\usepackage{amsmath,amssymb}\n"
                    "\\usepackage{natbib}\n"
                    "\\graphicspath{{figures/}{tables/}}\n"
                    "\\title{Research Paper Title}\n"
                    "\\author{Author Name}\n"
                    "\\begin{document}\n"
                    "\\maketitle\n"
                    "\\input{sections/abstract}\n"
                    "\\input{sections/introduction}\n"
                    "\\input{sections/related_work}\n"
                    "\\input{sections/methodology}\n"
                    "\\input{sections/experiments}\n"
                    "\\input{sections/results}\n"
                    "\\input{sections/discussion}\n"
                    "\\input{sections/conclusion}\n"
                    "\\bibliographystyle{plain}\n"
                    "\\bibliography{references}\n"
                    "\\end{document}\n"
                )

                # Create section files
                sections = {
                    "abstract.tex": (
                        "\\begin{abstract}\n"
                        "This paper presents novel research in the field.\n"
                        "\\end{abstract}\n"
                    ),
                    "introduction.tex": (
                        "\\section{Introduction}\n"
                        "\\label{sec:intro}\n"
                        "The introduction provides background on the research area.\n"
                        "Figure~\\ref{fig:overview} shows the general approach.\n"
                        "\\begin{figure}[htbp]\n"
                        "\\centering\n"
                        "\\includegraphics[width=0.8\\textwidth]{overview}\n"
                        "\\caption{Research overview}\n"
                        "\\label{fig:overview}\n"
                        "\\end{figure}\n"
                    ),
                    "related_work.tex": (
                        "\\section{Related Work}\n"
                        "\\label{sec:related}\n"
                        "Previous work in this area includes various approaches.\n"
                    ),
                    "methodology.tex": (
                        "\\section{Methodology}\n"
                        "\\label{sec:method}\n"
                        "Our methodology consists of several steps:\n"
                        "\\begin{enumerate}\n"
                        "\\item Data collection\n"
                        "\\item Preprocessing\n"
                        "\\item Analysis\n"
                        "\\end{enumerate}\n"
                        "\\input{sections/method_details}\n"
                    ),
                    "method_details.tex": (
                        "\\subsection{Implementation Details}\n"
                        "The implementation uses the following algorithm:\n"
                        "\\begin{equation}\n"
                        "f(x) = \\sum_{i=1}^{n} w_i x_i\n"
                        "\\label{eq:algorithm}\n"
                        "\\end{equation}\n"
                    ),
                    "experiments.tex": (
                        "\\section{Experiments}\n"
                        "\\label{sec:experiments}\n"
                        "We conducted experiments on multiple datasets.\n"
                        "Table~\\ref{tab:datasets} summarizes the datasets used.\n"
                        "\\input{tables/dataset_table}\n"
                    ),
                    "results.tex": (
                        "\\section{Results}\n"
                        "\\label{sec:results}\n"
                        "The experimental results are shown in Figure~\\ref{fig:results}.\n"
                        "\\begin{figure}[htbp]\n"
                        "\\centering\n"
                        "\\includegraphics[width=0.9\\textwidth]{results_plot}\n"
                        "\\caption{Experimental results}\n"
                        "\\label{fig:results}\n"
                        "\\end{figure}\n"
                    ),
                    "discussion.tex": (
                        "\\section{Discussion}\n"
                        "\\label{sec:discussion}\n"
                        "The results demonstrate the effectiveness of our approach.\n"
                        "As shown in Equation~\\ref{eq:algorithm}, the method is efficient.\n"
                    ),
                    "conclusion.tex": (
                        "\\section{Conclusion}\n"
                        "\\label{sec:conclusion}\n"
                        "In conclusion, we have presented a novel approach that achieves good results.\n"
                        "Future work will explore extensions to other domains.\n"
                    ),
                }

                # Create table file
                table_content = (
                    "\\begin{table}[htbp]\n"
                    "\\centering\n"
                    "\\begin{tabular}{|l|c|c|}\n"
                    "\\hline\n"
                    "Dataset & Size & Type \\\\\n"
                    "\\hline\n"
                    "Dataset A & 1000 & Training \\\\\n"
                    "Dataset B & 500 & Testing \\\\\n"
                    "\\hline\n"
                    "\\end{tabular}\n"
                    "\\caption{Datasets used in experiments}\n"
                    "\\label{tab:datasets}\n"
                    "\\end{table}\n"
                )

                # Create files
                with open("main.tex", "w") as f:
                    f.write(main_content)

                for filename, content in sections.items():
                    with open(f"sections/{filename}", "w") as f:
                        f.write(content)

                with open("tables/dataset_table.tex", "w") as f:
                    f.write(table_content)

                # Create figure files
                figures = ["overview.pdf", "results_plot.png"]
                for fig in figures:
                    with open(f"figures/{fig}", "wb") as f:
                        f.write(f"fake {fig} data".encode())

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify all sections are included
                assert "\\section{Introduction}" in result
                assert "\\section{Related Work}" in result
                assert "\\section{Methodology}" in result
                assert "\\subsection{Implementation Details}" in result
                assert "\\section{Experiments}" in result
                assert "\\section{Results}" in result
                assert "\\section{Discussion}" in result
                assert "\\section{Conclusion}" in result

                # Verify graphics are processed
                assert "\\includegraphics[width=0.8\\textwidth]{overview.pdf}" in result
                assert (
                    "\\includegraphics[width=0.9\\textwidth]{results_plot.png}"
                    in result
                )

                # Verify figures are copied
                assert os.path.exists("output/overview.pdf")
                assert os.path.exists("output/results_plot.png")

                # Verify tables are included
                assert "\\begin{tabular}" in result
                assert "Dataset A" in result

                # Verify references and equations are preserved
                assert "\\label{sec:intro}" in result
                assert "\\ref{fig:overview}" in result
                assert "\\ref{eq:algorithm}" in result
                assert "\\sum_{i=1}^{n} w_i x_i" in result

            finally:
                os.chdir(original_cwd)

    def test_thesis_document_structure(self) -> None:
        """Test thesis-like document with chapters and bibliography."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create thesis structure
                os.makedirs("chapters")
                os.makedirs("appendices")
                os.makedirs("figures")

                # Main thesis document
                main_content = (
                    "\\documentclass[12pt]{book}\n"
                    "\\usepackage{graphicx}\n"
                    "\\usepackage{natbib}\n"
                    "\\graphicspath{{figures/}}\n"
                    "\\title{PhD Thesis}\n"
                    "\\author{Student Name}\n"
                    "\\begin{document}\n"
                    "\\frontmatter\n"
                    "\\maketitle\n"
                    "\\input{chapters/abstract}\n"
                    "\\tableofcontents\n"
                    "\\listoffigures\n"
                    "\\listoftables\n"
                    "\\mainmatter\n"
                    "\\input{chapters/introduction}\n"
                    "\\input{chapters/literature_review}\n"
                    "\\input{chapters/methodology}\n"
                    "\\input{chapters/results}\n"
                    "\\input{chapters/conclusion}\n"
                    "\\appendix\n"
                    "\\input{appendices/additional_data}\n"
                    "\\backmatter\n"
                    "\\bibliographystyle{alpha}\n"
                    "\\bibliography{thesis_refs}\n"
                    "\\end{document}\n"
                )

                # Create chapter files
                chapters = {
                    "abstract.tex": (
                        "\\begin{abstract}\n"
                        "This thesis investigates important research questions.\n"
                        "\\end{abstract}\n"
                    ),
                    "introduction.tex": (
                        "\\chapter{Introduction}\n"
                        "\\label{chap:intro}\n"
                        "\\section{Motivation}\n"
                        "The motivation for this research comes from practical needs.\n"
                        "\\section{Research Questions}\n"
                        "The main research questions are:\n"
                        "\\begin{enumerate}\n"
                        "\\item How can we improve current methods?\n"
                        "\\item What are the limitations?\n"
                        "\\end{enumerate}\n"
                        "\\section{Contributions}\n"
                        "This thesis makes the following contributions:\n"
                        "\\input{chapters/contributions}\n"
                    ),
                    "contributions.tex": (
                        "\\begin{itemize}\n"
                        "\\item Novel algorithm development\n"
                        "\\item Comprehensive evaluation\n"
                        "\\item Theoretical analysis\n"
                        "\\end{itemize}\n"
                    ),
                    "literature_review.tex": (
                        "\\chapter{Literature Review}\n"
                        "\\label{chap:literature}\n"
                        "\\section{Background}\n"
                        "The field has evolved significantly over the past decade.\n"
                        "\\section{Related Work}\n"
                        "Previous research can be categorized into several areas.\n"
                    ),
                    "methodology.tex": (
                        "\\chapter{Methodology}\n"
                        "\\label{chap:method}\n"
                        "\\section{Approach}\n"
                        "Our approach is based on the following principles.\n"
                        "Figure~\\ref{fig:architecture} shows the system architecture.\n"
                        "\\begin{figure}[htbp]\n"
                        "\\centering\n"
                        "\\includegraphics[width=\\textwidth]{architecture}\n"
                        "\\caption{System architecture}\n"
                        "\\label{fig:architecture}\n"
                        "\\end{figure}\n"
                    ),
                    "results.tex": (
                        "\\chapter{Results and Evaluation}\n"
                        "\\label{chap:results}\n"
                        "\\section{Experimental Setup}\n"
                        "The experiments were conducted under controlled conditions.\n"
                        "\\section{Results}\n"
                        "The results demonstrate the effectiveness of our approach.\n"
                    ),
                    "conclusion.tex": (
                        "\\chapter{Conclusion}\n"
                        "\\label{chap:conclusion}\n"
                        "\\section{Summary}\n"
                        "This thesis has presented a comprehensive study.\n"
                        "\\section{Future Work}\n"
                        "Future research directions include several areas.\n"
                    ),
                }

                # Create appendix
                appendix_content = (
                    "\\chapter{Additional Experimental Data}\n"
                    "\\label{app:data}\n"
                    "This appendix contains additional experimental data.\n"
                    "\\section{Dataset Details}\n"
                    "Detailed information about datasets used.\n"
                )

                # Create files
                with open("main.tex", "w") as f:
                    f.write(main_content)

                for filename, content in chapters.items():
                    with open(f"chapters/{filename}", "w") as f:
                        f.write(content)

                with open("appendices/additional_data.tex", "w") as f:
                    f.write(appendix_content)

                # Create figure
                with open("figures/architecture.pdf", "wb") as f:
                    f.write(b"architecture diagram data")

                os.makedirs("output")

                # Test flattening
                config = LatexExpandConfig(root_directory=".")
                expander = LatexExpander(config)
                result = expander.flatten_latex("main.tex", "output/main_flat.tex")

                # Verify thesis structure elements
                assert "\\frontmatter" in result
                assert "\\mainmatter" in result
                assert "\\backmatter" in result
                assert "\\appendix" in result

                # Verify all chapters are included
                assert "\\chapter{Introduction}" in result
                assert "\\chapter{Literature Review}" in result
                assert "\\chapter{Methodology}" in result
                assert "\\chapter{Results and Evaluation}" in result
                assert "\\chapter{Conclusion}" in result
                assert "\\chapter{Additional Experimental Data}" in result

                # Verify nested includes work
                assert "Novel algorithm development" in result

                # Verify figure processing
                assert (
                    "\\includegraphics[width=\\textwidth]{architecture.pdf}" in result
                )
                assert os.path.exists("output/architecture.pdf")

            finally:
                os.chdir(original_cwd)
