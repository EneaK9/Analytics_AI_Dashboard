/**
 * Platform Toggle Component
 * Provides a toggle between Shopify and Amazon platforms for inventory analytics
 */

import React from "react";
import { ShoppingCart, Package2 } from "lucide-react";

interface PlatformToggleProps {
  selectedPlatform: "shopify" | "amazon";
  onPlatformChange: (platform: "shopify" | "amazon") => void;
  className?: string;
}

export default function PlatformToggle({
  selectedPlatform,
  onPlatformChange,
  className = "",
}: PlatformToggleProps) {
  return (
    <div className={`flex items-center space-x-2 bg-gray-100 rounded-lg p-1 ${className}`}>
      <button
        onClick={() => onPlatformChange("shopify")}
        className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          selectedPlatform === "shopify"
            ? "bg-white text-green-700 shadow-sm"
            : "text-gray-600 hover:text-gray-900"
        }`}
        aria-label="Switch to Shopify data"
      >
        <ShoppingCart className="h-4 w-4" />
        <span>Shopify</span>
      </button>
      <button
        onClick={() => onPlatformChange("amazon")}
        className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          selectedPlatform === "amazon"
            ? "bg-white text-orange-700 shadow-sm"
            : "text-gray-600 hover:text-gray-900"
        }`}
        aria-label="Switch to Amazon data"
      >
        <Package2 className="h-4 w-4" />
        <span>Amazon</span>
      </button>
    </div>
  );
}
