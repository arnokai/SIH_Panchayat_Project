// src/data/mockLocations.js
export const locationHierarchy = {
  "North 24 Parganas": {
    blocks: {
      "Amdanga": ["AMDANGA", "Bodai", "Maricha", "Tarulia"],
      "Barasat-I": ["Barasat Town", "Chapra", "Duttapukur", "Kadambagachi"],
      "Habra-I": ["Habra", "Bira", "Prithu", "Jadurberia"],
      "Basirhat-I": ["Itinda", "Pally", "Mathurapur"]
    }
  },
  "Nadia": {
    blocks: {
      "Krishnagar-I": ["Krishnagar Sadar", "Bhaluka", "Dignagar", "Bara Andulbaria"],
      "Ranaghat-I": ["Ranaghat Rural", "Kamaragachi", "Baidyapur", "Nabagram"],
      "Tehatta-I": ["Tehatta", "Kanainagar", "Ghatpara"]
    }
  },
  "Purba Bardhaman": {
    blocks: {
      "Burdwan-I": ["Burdwan Sadar", "Saraitor", "Belrum", "Barai"],
      "Memari-I": ["Memari Town", "Bhanowar", "Satgachia", "Pahalanpur"],
      "Katwa-I": ["Katwa Rural", "Srikhanda", "Aliganj"]
    }
  },
  "Bankura": {
    blocks: {
      "Bankura-I": ["Anchra", "Onda", "Sabrakona"],
      "Bishnupur": ["Bishnupur Rural", "Radhanagar", "Kendua"]
    }
  }
};

// Map actual district/panchayat names to unique IDs for your Python backend
export const panchayatIdMap = {
  "AMDANGA": "107778",
  "Bodai": "107779",
  "Maricha": "107780",
  "Barasat Town": "107781",
  "Krishnagar Sadar": "107782",
  "Burdwan Sadar": "107783",
  "Habra": "107784",
  "Ranaghat Rural": "107785"
};

export const DEFAULT_PANCHAYAT_ID = "107778";