/* ════════════════════════════════════════════════════════════════
   Client-side PDF Export using jsPDF
   ════════════════════════════════════════════════════════════════ */

window.exportToPDF = function(elementId, title) {
    const { jsPDF } = window.jspdf;
    if (!jsPDF) {
        showToast('PDF library not loaded', 'error');
        return;
    }

    const doc = new jsPDF();
    const element = document.getElementById(elementId);

    if (!element) {
        showToast('Content element not found', 'error');
        return;
    }

    // Capture text content
    const text = element.innerText || element.textContent;
    const lines = doc.splitTextToSize(text, 180);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.text(title, 14, 22);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);
    
    let y = 35;
    lines.forEach(line => {
        if (y > 280) {
            doc.addPage();
            y = 20;
        }
        doc.text(line, 14, y);
        y += 7;
    });

    doc.save(`${title.toLowerCase().replace(/\s+/g, '_')}.pdf`);
    showToast('PDF downloaded successfully!', 'success');
};
