import React, { useState, useEffect } from "react";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "./components/ui/hover-card";

const Message = ({ message }) => {
  const { text, isBot, timestamp, sources, isError, summary, suggestions } =
    message;

  const is_greeting = message.is_greeting || false;

  const [processedText, setProcessedText] = useState("");
  const [referencesMap, setReferencesMap] = useState({});

  const formatTime = (date) => {
    return date.toLocaleTimeString("id-ID", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Process sources to create references map
  useEffect(() => {
    if (sources && sources.length > 0 && text) {
      const refMap = {};
      sources.forEach((source, index) => {
        const refNumber = index + 1;

        // Extract document name and info from source
        let docName = "";
        let docInfo = "";

        if (source.includes("Dokumen:")) {
          const parts = source.split("Informasi:");
          if (parts.length >= 2) {
            docName = parts[0].replace("Dokumen:", "").trim();
            docInfo = parts[1].trim();
          } else {
            docName = source.replace("Dokumen:", "").trim();
            docInfo = "Lihat dokumen untuk detail lengkap";
          }
        } else {
          // Fallback for other formats
          const match = source.match(/^(.+?\.docx)/);
          if (match) {
            docName = match[1];
            docInfo = source.substring(match[0].length + 1).trim();
          } else {
            docName = `Referensi ${refNumber}`;
            docInfo = source;
          }
        }

        refMap[refNumber] = {
          docName,
          docInfo: docInfo || "Informasi detail tersedia di dokumen",
        };
      });

      setReferencesMap(refMap);

      // Add placeholder markers for reference numbers (will be replaced with components)
      let modifiedText = text;
      const referensiRegex = /\*\*Referensi:\*\*\s*([^\n]+)/gi;
      let match;
      let refCounter = 1;

      while ((match = referensiRegex.exec(text)) !== null) {
        if (refCounter <= sources.length) {
          const originalRef = match[0];
          // Add marker that will be replaced with React component
          const replacement = `${originalRef}{{REF_${refCounter}}}`;
          modifiedText = modifiedText.replace(originalRef, replacement);
          refCounter++;
        }
      }

      setProcessedText(modifiedText);
    } else {
      setProcessedText(text);
    }
  }, [text, sources]);

  // Function to format text with enhanced markdown-like formatting
  const formatText = (text) => {
    if (!text) return text;

    // Escape HTML first to prevent XSS
    let formatted = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Convert **bold** to <strong> (before line breaks to preserve bold across lines)
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Convert *italic* to <em> (not preceded by *, to avoid matching bold)
    formatted = formatted.replace(
      /(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)/g,
      "<em>$1</em>"
    );

    // Convert line breaks to <br>
    formatted = formatted.replace(/\n/g, "<br>");

    // Convert numbered lists with bold (1. 2. 3.) and add spacing
    formatted = formatted.replace(
      /^(\d+\.\s+\*\*.*?\*\*)/gm,
      '<br><strong style="font-size: 1.05em;">$1</strong>'
    );
    formatted = formatted.replace(/^(\d+\.\s+)/gm, "<br><strong>$1</strong>");

    // Convert bullet points (• or - or *) with proper indentation
    formatted = formatted.replace(/^•\s+/gm, "<br>&nbsp;&nbsp;&nbsp;• ");
    formatted = formatted.replace(/^[-]\s+/gm, "<br>&nbsp;&nbsp;&nbsp;• ");

    // Add extra spacing after referensi/reference sections
    formatted = formatted.replace(
      /(\*\*Referensi:\*\*[^<]+)(<br>)/g,
      "$1<br><br>"
    );

    // Convert ## headers to bold with larger size
    formatted = formatted.replace(
      /^##\s(.+)$/gm,
      '<strong style="font-size: 1.1em;">$1</strong>'
    );

    // Add spacing between major sections (after bold headings followed by colon)
    formatted = formatted.replace(/(\*\*[^*]+:\*\*)(<br>)/g, "<br>$1<br>");

    // Clean up multiple consecutive <br> tags (max 2)
    formatted = formatted.replace(/(<br>){3,}/g, "<br><br>");

    return formatted;
  };

  // Component to render text with inline reference hover cards
  const ReferenceText = () => {
    const formattedText = processedText || text;

    // Split text by reference markers to insert HoverCard components
    const renderTextWithReferences = () => {
      if (
        !sources ||
        sources.length === 0 ||
        !formattedText.includes("{{REF_")
      ) {
        return (
          <div
            dangerouslySetInnerHTML={{ __html: formatText(formattedText) }}
          />
        );
      }

      // Split by reference markers {{REF_X}} before formatting
      const segments = formattedText.split(/(\{\{REF_\d+\}\})/g);
      const parts = [];

      segments.forEach((segment, index) => {
        // Check if this segment is a reference marker
        const refMatch = segment.match(/\{\{REF_(\d+)\}\}/);

        if (refMatch) {
          const refNum = refMatch[1];
          const refData = referencesMap[refNum];

          if (refData) {
            parts.push(
              <HoverCard
                key={`ref-${refNum}-${index}`}
                openDelay={0}
                closeDelay={100}
              >
                <HoverCardTrigger asChild>
                  <span
                    className="ref-link inline-block"
                    style={{
                      cursor: "pointer",
                      position: "relative",
                      zIndex: 10,
                    }}
                  >
                    [{refNum}]
                  </span>
                </HoverCardTrigger>
                <HoverCardContent
                  className="w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-xl z-50"
                  side="top"
                  align="start"
                  sideOffset={10}
                >
                  <div className="space-y-2.5">
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-1.5 border-b border-gray-100 dark:border-gray-700 pb-2">
                      <span>📚</span>
                      <span>Referensi [{refNum}]</span>
                    </h4>
                    <div className="space-y-1">
                      <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                        Dokumen:
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                        {refData.docName}
                      </p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                        Informasi:
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                        {refData.docInfo}
                      </p>
                    </div>
                  </div>
                </HoverCardContent>
              </HoverCard>
            );
          }
        } else if (segment) {
          // Regular text segment - format to HTML
          parts.push(
            <span
              key={`text-${index}`}
              dangerouslySetInnerHTML={{ __html: formatText(segment) }}
            />
          );
        }
      });

      return <>{parts}</>;
    };

    return (
      <div
        className="text-sm sm:text-base leading-loose whitespace-pre-wrap reference-container w-full"
        style={{
          lineHeight: "1.8",
          wordSpacing: "0.05em",
          letterSpacing: "0.01em",
        }}
      >
        {renderTextWithReferences()}
      </div>
    );
  };

  // Add click handlers for reference links after component mounts
  useEffect(() => {
    const handleRefClick = (e) => {
      if (
        e.target.classList.contains("ref-link") ||
        e.target.closest(".ref-link")
      ) {
        e.preventDefault();
        e.stopPropagation();
      }
    };

    document.addEventListener("click", handleRefClick);
    return () => document.removeEventListener("click", handleRefClick);
  }, []);

  // Render reference badges at bottom with compact hover cards
  const ReferenceLinks = () => {
    if (!sources || sources.length === 0 || !isBot || is_greeting) return null;

    return (
      <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 flex flex-wrap gap-2">
        {Object.entries(referencesMap).map(([refNum, refData]) => (
          <HoverCard key={refNum} openDelay={200} closeDelay={100}>
            <HoverCardTrigger asChild>
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors border border-gray-200 dark:border-gray-600">
                <span className="text-[10px]">📄</span>
                <span className="font-mono text-[10px]">[{refNum}]</span>
                <span className="truncate max-w-[120px] text-[11px]">
                  {refData.docName.replace(".docx", "").substring(0, 25)}...
                </span>
              </span>
            </HoverCardTrigger>
            <HoverCardContent
              className="w-72 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-lg p-3 z-[9999]"
              side="top"
              align="start"
              sideOffset={5}
            >
              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <span className="text-sm">📚</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-gray-900 dark:text-gray-100 mb-1">
                      Referensi [{refNum}]
                    </p>
                    <p className="text-xs text-gray-700 dark:text-gray-300 font-medium mb-2 leading-snug">
                      {refData.docName}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                      {refData.docInfo.length > 150
                        ? refData.docInfo.substring(0, 150) + "..."
                        : refData.docInfo}
                    </p>
                  </div>
                </div>
              </div>
            </HoverCardContent>
          </HoverCard>
        ))}
      </div>
    );
  };

  return (
    <div
      className={`flex ${isBot ? "justify-start" : "justify-end"} w-full group`}
    >
      <div
        className={`${isBot ? "w-full" : "max-w-[75%]"} px-5 py-4 rounded-2xl ${
          isBot
            ? isError
              ? "bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800"
              : "bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700"
            : "bg-blue-600 dark:bg-blue-500 text-white shadow-sm"
        }`}
      >
        <ReferenceText />

        {/* Summary Section */}
        {summary && isBot && (
          <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
            <h4 className="text-sm font-semibold text-amber-900 dark:text-amber-200 mb-2 flex items-center gap-2">
              <span>📝</span>
              <span>Kesimpulan</span>
            </h4>
            <div
              className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed"
              style={{ lineHeight: "1.6" }}
              dangerouslySetInnerHTML={{ __html: formatText(summary) }}
            />
          </div>
        )}

        {/* Suggestions Section */}
        {suggestions && isBot && (
          <div className="mt-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
            <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2 flex items-center gap-2">
              <span>💡</span>
              <span>Saran</span>
            </h4>
            <div
              className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed"
              style={{ lineHeight: "1.6" }}
              dangerouslySetInnerHTML={{ __html: formatText(suggestions) }}
            />
          </div>
        )}

        {/* Reference Links with Hover Cards */}
        <ReferenceLinks />

        {/* OLD: Sources Section with Accordion - Commented out
        {isBot && !is_greeting && (
          <div className="mt-3 pt-3 border-t border-green-400 dark:border-gray-500">
            {sources && sources.length > 0 ? (
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="sources" className="border-none">
                  <AccordionTrigger className="text-xs font-semibold text-green-700 dark:text-green-300 hover:no-underline py-2">
                    <span className="flex items-center gap-2">
                      📚 Sumber Referensi ({sources.length})
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="pt-0 pb-2">
                    <div className="space-y-3">
                      {sources
                        .map((source, index) => {
                          // Check if this is a document-specific answer with filename
                          const filenameMatch =
                            source.match(/^(.+\.docx): (.+)$/s);

                          if (filenameMatch) {
                            const filename = filenameMatch[1];
                            const docContent = filenameMatch[2];

                            // Skip if no relevant information
                            if (
                              docContent.includes("Tidak ada informasi relevan")
                            ) {
                              return null;
                            }

                            return (
                              <Accordion
                                key={index}
                                type="single"
                                collapsible
                                className="w-full"
                              >
                                <AccordionItem
                                  value={`doc-${index}`}
                                  className="border border-green-200 dark:border-gray-600 rounded-lg"
                                >
                                  <AccordionTrigger className="text-xs font-semibold text-green-700 dark:text-green-300 hover:no-underline py-2 px-3">
                                    <span className="flex items-center gap-2">
                                      📄 {filename}
                                    </span>
                                  </AccordionTrigger>
                                  <AccordionContent className="pt-0 pb-2 px-3">
                                    <div className="p-4 bg-gradient-to-r from-green-100 to-yellow-100 dark:from-gray-600 dark:to-gray-500 rounded-lg border border-green-300 dark:border-gray-400">
                                      <div
                                        className="text-sm text-green-700 dark:text-green-300 leading-relaxed"
                                        dangerouslySetInnerHTML={{
                                          __html: formatText(docContent),
                                        }}
                                      />
                                    </div>
                                  </AccordionContent>
                                </AccordionItem>
                              </Accordion>
                            );
                          }

                          // Check if this is a document-specific answer (starting with "Dokumen X:")
                          const isDocumentAnswer =
                            source.startsWith("Dokumen ");

                          if (isDocumentAnswer) {
                            // Extract document number and content
                            const match = source.match(
                              /^Dokumen (\d+): (.+)$/s
                            );
                            if (match) {
                              const docNumber = match[1];
                              const docContent = match[2];

                              // Skip if no relevant information
                              if (
                                docContent.includes(
                                  "Tidak ada informasi relevan"
                                )
                              ) {
                                return null;
                              }

                              return (
                                <Accordion
                                  key={index}
                                  type="single"
                                  collapsible
                                  className="w-full"
                                >
                                  <AccordionItem
                                    value={`doc-${docNumber}`}
                                    className="border border-green-200 dark:border-gray-600 rounded-lg"
                                  >
                                    <AccordionTrigger className="text-xs font-semibold text-green-700 dark:text-green-300 hover:no-underline py-2 px-3">
                                      <span className="flex items-center gap-2">
                                        📄 Dokumen {docNumber}
                                      </span>
                                    </AccordionTrigger>
                                    <AccordionContent className="pt-0 pb-2 px-3">
                                      <div className="p-4 bg-gradient-to-r from-green-100 to-yellow-100 dark:from-gray-600 dark:to-gray-500 rounded-lg border border-green-300 dark:border-gray-400">
                                        <div
                                          className="text-sm text-green-700 dark:text-green-300 leading-relaxed"
                                          dangerouslySetInnerHTML={{
                                            __html: formatText(docContent),
                                          }}
                                        />
                                      </div>
                                    </AccordionContent>
                                  </AccordionItem>
                                </Accordion>
                              );
                            }
                          }

                          // Fallback for other source formats
                          return (
                            <div
                              key={index}
                              className="p-2 bg-green-50 dark:bg-gray-700 rounded border border-green-200 dark:border-gray-600"
                            >
                              <span className="font-medium text-green-800 dark:text-green-200 text-xs">
                                [Sumber {index + 1}]
                              </span>{" "}
                              <span className="text-xs text-green-600 dark:text-green-400">
                                {source}
                              </span>
                            </div>
                          );
                        })
                        .filter(Boolean)}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            ) : (
              <div className="text-xs font-semibold text-green-700 dark:text-green-300 py-2">
                <span className="flex items-center gap-2">
                  📚 Sumber Referensi (0)
                </span>
              </div>
            )}
          </div>
        )}
        */}

        <p
          className={`text-xs mt-3 ${
            isBot
              ? "text-gray-500 dark:text-gray-400"
              : "text-blue-100 dark:text-blue-200"
          }`}
        >
          {formatTime(timestamp)}
        </p>
      </div>
    </div>
  );
};

export default Message;
