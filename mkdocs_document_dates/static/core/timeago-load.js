if (typeof window.document$ !== 'undefined' && !window.document$.isStopped) {
    window.document$.subscribe(window.renderDocumentDates);
} else {
    window.renderDocumentDates();
}