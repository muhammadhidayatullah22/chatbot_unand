import React, { useState, useEffect, useCallback } from "react";

const TelegramButton = () => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Set posisi default di sebelah kiri tombol mode gelap
  useEffect(() => {
    const updateDefaultPosition = () => {
      const isMobile = window.innerWidth < 768;
      // Posisi di sebelah kiri ThemeToggle (sekitar 120px dari kanan untuk desktop, 100px untuk mobile)
      setPosition({
        x: window.innerWidth - (isMobile ? 128 : 160), // Lebih ke kiri dari ThemeToggle
        y: isMobile ? 16 : 24, // top-4 untuk mobile, top-6 untuk desktop
      });
    };

    updateDefaultPosition();
    window.addEventListener("resize", updateDefaultPosition);
    return () => window.removeEventListener("resize", updateDefaultPosition);
  }, []);

  const handleClick = () => {
    if (!isDragging) {
      // Ganti dengan URL Telegram bot yang sesuai
      window.open("https://t.me/ChatbotUnand_bot", "_blank");
    }
  };

  const handleMouseDown = (e) => {
    setIsDragging(false);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  };

  const handleMouseMove = useCallback(
    (e) => {
      if (dragStart.x !== 0 || dragStart.y !== 0) {
        setIsDragging(true);
        const newX = e.clientX - dragStart.x;
        const newY = e.clientY - dragStart.y;

        // Batasi posisi agar tidak keluar dari viewport
        const buttonSize = window.innerWidth < 768 ? 56 : 64; // 14*4 atau 16*4
        const maxX = window.innerWidth - buttonSize;
        const maxY = window.innerHeight - buttonSize;

        setPosition({
          x: Math.max(0, Math.min(newX, maxX)),
          y: Math.max(0, Math.min(newY, maxY)),
        });
      }
    },
    [dragStart.x, dragStart.y]
  );

  const handleMouseUp = useCallback(() => {
    setDragStart({ x: 0, y: 0 });
    setTimeout(() => setIsDragging(false), 100); // Delay untuk mencegah click setelah drag
  }, []);

  const handleTouchStart = (e) => {
    const touch = e.touches[0];
    setIsDragging(false);
    setDragStart({
      x: touch.clientX - position.x,
      y: touch.clientY - position.y,
    });
    setShowTooltip(true);
  };

  const handleTouchMove = (e) => {
    e.preventDefault();
    const touch = e.touches[0];
    if (dragStart.x !== 0 || dragStart.y !== 0) {
      setIsDragging(true);
      const newX = touch.clientX - dragStart.x;
      const newY = touch.clientY - dragStart.y;

      // Batasi posisi agar tidak keluar dari viewport
      const buttonSize = window.innerWidth < 768 ? 56 : 64;
      const maxX = window.innerWidth - buttonSize;
      const maxY = window.innerHeight - buttonSize;

      setPosition({
        x: Math.max(0, Math.min(newX, maxX)),
        y: Math.max(0, Math.min(newY, maxY)),
      });
    }
  };

  const handleTouchEnd = () => {
    setDragStart({ x: 0, y: 0 });
    if (!isDragging) {
      setTimeout(() => setShowTooltip(false), 1500);
    } else {
      setShowTooltip(false);
      setTimeout(() => setIsDragging(false), 100);
    }
  };

  useEffect(() => {
    if (dragStart.x !== 0 || dragStart.y !== 0) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [dragStart, handleMouseMove, handleMouseUp]);

  return (
    <div
      className="fixed z-50 cursor-move select-none"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transition: isDragging ? "none" : "all 0.2s ease",
      }}
    >
      {showTooltip && (
        <div className="absolute top-16 right-0 bg-gray-800 dark:bg-gray-700 text-white text-xs md:text-sm rounded-lg py-1 px-2 md:py-2 md:px-3 shadow-lg w-40 md:w-48 text-center">
          Chat di Telegram dengan ChatBot Unand
          <div className="absolute top-0 right-6 transform -translate-y-1/2 rotate-45 w-2 h-2 bg-gray-800 dark:bg-gray-700"></div>
        </div>
      )}
      <button
        onClick={handleClick}
        onMouseDown={handleMouseDown}
        onMouseEnter={() => !isDragging && setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        className="w-14 h-14 md:w-16 md:h-16 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105 active:scale-95 border-2 border-white"
        style={{
          cursor: isDragging ? "grabbing" : "grab",
          userSelect: "none",
          touchAction: "none",
        }}
        aria-label="Chat di Telegram dengan tanyo unand"
        title="Chat di Telegram dengan tanyo unand"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="w-7 h-7 md:w-8 md:h-8 text-white"
          viewBox="0 0 24 24"
          fill="currentColor"
          strokeWidth="0"
        >
          <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.96 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
        </svg>
      </button>
    </div>
  );
};

export default TelegramButton;
