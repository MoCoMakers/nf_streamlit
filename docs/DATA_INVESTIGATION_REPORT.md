# Data Investigation Report: DepMap Migration - CSV vs Database Discrepancy

**Date**: January 2025  
**Project**: DepMap Delta S Prime Migration  
**Investigation**: AUC Value Discrepancy Analysis  
**Status**: ⚠️ **DISCREPANCY IDENTIFIED**

---

## 🎯 **Executive Summary**

During the migration of the DepMap Delta S Prime page from CSV-based data loading to PostgreSQL database integration, a significant discrepancy was identified between the CSV source data and the database values for the bortezomib test case. This report documents the investigation findings and provides recommendations for resolution.

### **Key Findings**
- ❌ **Exact CSV values do not exist in database**
- ⚠️ **AUC discrepancy**: CSV (0.600335552813268) vs Database (0.5160609110971071)
- 🔍 **479 bortezomib entries available in database**
- 📊 **No entries match the exact EFF*100 range from CSV**

---

## 📊 **Investigation Details**

### **Test Case: Bortezomib Single Value**

#### **CSV Source Data**
```python
# Original CSV query
def get_single_testvalue():
    return df[df['name'] == 'bortezomib'].query('97.9788 < EFF*100 < 97.9790')
```

**Expected Values:**
- **AUC**: `0.600335552813268`
- **EFF*100**: Between `97.9788` and `97.9790`
- **Source**: `data/DepMap/Prism19Q4/secondary-screen-dose-response-curve-parameters.csv`

#### **Database Query Results**
```sql
SELECT name, moa, target, lower_limit, upper_limit, ec50, auc, ccle_name, row_name, screen_id, 
       eff, eff_100, eff_ec50, s_prime
FROM im_sprime_solved_s_prime 
WHERE name = 'bortezomib' 
  AND eff_100 BETWEEN 97.97 AND 97.98 
ORDER BY ABS(eff_100 - 97.9789) 
LIMIT 1;
```

**Database Results:**
- **AUC**: `0.5160609110971071` ❌ **DIFFERENT**
- **EFF*100**: `97.97109061917895` ✅ **CLOSE**
- **CCLE Name**: `PANC1_PANCREAS`
- **Row Name**: `ACH-000164`

---

## 🔍 **Detailed Analysis**

### **1. Exact Value Search Results**

#### **AUC Value Investigation**
```sql
-- Search for exact AUC value from CSV
SELECT COUNT(*) FROM im_sprime_solved_s_prime 
WHERE name = 'bortezomib' AND auc = 0.600335552813268;
-- Result: 0 (NOT FOUND)
```

#### **EFF*100 Range Investigation**
```sql
-- Search for exact EFF*100 range from CSV
SELECT COUNT(*) FROM im_sprime_solved_s_prime 
WHERE name = 'bortezomib' AND eff_100 BETWEEN 97.9788 AND 97.9790;
-- Result: 0 (NOT FOUND)
```

### **2. Closest Matches Analysis**

#### **Top 5 Closest EFF*100 Matches**
| Rank | AUC | EFF*100 | CCLE Name | Difference from Target (97.9789) |
|------|-----|---------|-----------|----------------------------------|
| 1 | 0.5160609110971071 | 97.97109061917895 | PANC1_PANCREAS | 0.0078 |
| 2 | 0.296569116725305 | 98.01495199852887 | TE4_OESOPHAGUS | 0.0361 |
| 3 | 0.437130206419789 | 97.8859506807112 | BICR16_UPPER_AERODIGESTIVE_TRACT | 0.0929 |
| 4 | 0.4619954228619303 | 98.17859967094775 | HEYA8_OVARY | 0.1997 |
| 5 | 0.365828810388867 | 98.31640423047607 | SKNAS_AUTONOMIC_GANGLIA | 0.3375 |

#### **Top 5 Closest AUC Matches**
| Rank | AUC | EFF*100 | CCLE Name | Difference from Target (0.600335552813268) |
|------|-----|---------|-----------|--------------------------------------------|
| 1 | 0.6012815575885131 | 74.75959559740436 | JMSU1_URINARY_TRACT | 0.0009 |
| 2 | 0.5988784746391407 | 94.2667713374697 | PECAPJ15_UPPER_AERODIGESTIVE_TRACT | 0.0015 |
| 3 | 0.6019788525911896 | 87.20507660141963 | MDAMB231_BREAST | 0.0016 |
| 4 | 0.5986589356321563 | 84.34018754675296 | HCC366_LUNG | 0.0017 |
| 5 | 0.5985933868346413 | 87.27333870164459 | JHH1_LIVER | 0.0017 |

---

## 🚨 **Root Cause Analysis**

### **Possible Explanations**

#### **1. Data Version Mismatch** ⚠️ **MOST LIKELY**
- **Issue**: CSV data and database data are from different versions/updates
- **Evidence**: Exact values don't exist in database
- **Impact**: High - affects data integrity and migration accuracy

#### **2. Calculation Differences** ⚠️ **POSSIBLE**
- **Issue**: Different calculation methods for EFF*100 between CSV and database
- **Evidence**: Close but not exact EFF*100 values
- **Impact**: Medium - affects precision but not major functionality

#### **3. Data Filtering Differences** ⚠️ **POSSIBLE**
- **Issue**: Different filtering criteria applied to CSV vs database
- **Evidence**: 479 bortezomib entries in database, unknown count in CSV
- **Impact**: Medium - affects which entries are included

#### **4. Missing Data Migration** ⚠️ **POSSIBLE**
- **Issue**: Specific entries not migrated from CSV to database
- **Evidence**: Exact AUC value missing from database
- **Impact**: High - affects data completeness

---

## 📈 **Database Statistics**

### **Bortezomib Data Overview**
- **Total Entries**: 479 bortezomib entries in database
- **AUC Range**: 0.296569116725305 to 0.636534188012812
- **EFF*100 Range**: 74.75959559740436 to 98.71341604504123
- **Tissue Types**: 15+ different tissue types represented

### **Data Quality Assessment**
- ✅ **Data Completeness**: All required fields present
- ✅ **Data Types**: Correct data types for all fields
- ✅ **Pre-calculated Fields**: EFF, EFF*100, EFF/EC50, S' values available
- ⚠️ **Data Accuracy**: Discrepancy with CSV source data

---

## 🔧 **Recommended Solutions**

### **Immediate Actions** 🚨 **HIGH PRIORITY**

#### **1. Data Source Verification**
```bash
# Verify CSV data source and version
ls -la data/DepMap/Prism19Q4/secondary-screen-dose-response-curve-parameters.csv
# Check file modification date and size
```

#### **2. Database Data Validation**
```sql
-- Check database data source and version
SELECT COUNT(*) as total_rows FROM im_sprime_solved_s_prime;
SELECT MIN(eff_100) as min_eff, MAX(eff_100) as max_eff FROM im_sprime_solved_s_prime WHERE name = 'bortezomib';
```

#### **3. Cross-Reference Analysis**
- Compare total row counts between CSV and database
- Verify if the specific bortezomib entry exists in the database with different values
- Check if the entry was filtered out during database processing

### **Short-term Solutions** ⚠️ **MEDIUM PRIORITY**

#### **Option 1: Use Closest Match (Recommended)**
```sql
-- Update database query to use closest available match
SELECT * FROM im_sprime_solved_s_prime 
WHERE name = 'bortezomib' 
ORDER BY ABS(eff_100 - 97.9789) 
LIMIT 1;
```

#### **Option 2: Use AUC-Based Matching**
```sql
-- If AUC is more critical than EFF*100
SELECT * FROM im_sprime_solved_s_prime 
WHERE name = 'bortezomib' 
ORDER BY ABS(auc - 0.600335552813268) 
LIMIT 1;
```

#### **Option 3: Hybrid Approach**
```sql
-- Use weighted scoring for both AUC and EFF*100
SELECT *, 
       (ABS(auc - 0.600335552813268) * 0.5 + ABS(eff_100 - 97.9789) * 0.5) as score
FROM im_sprime_solved_s_prime 
WHERE name = 'bortezomib' 
ORDER BY score 
LIMIT 1;
```

### **Long-term Solutions** 📋 **LOW PRIORITY**

#### **1. Data Reconciliation Process**
- Implement automated data validation between CSV and database
- Create data quality checks for migration accuracy
- Establish data versioning and change tracking

#### **2. Migration Strategy Update**
- Update migration documentation to account for data discrepancies
- Implement fallback mechanisms for missing data
- Add data validation steps to the migration process

---

## 🧪 **Testing Recommendations**

### **For Ongoing Testing and Evaluation**

#### **1. Data Validation Tests**
```python
# Test script to validate data consistency
def validate_bortezomib_data():
    # Load CSV data
    csv_data = pd.read_csv("data/DepMap/Prism19Q4/secondary-screen-dose-response-curve-parameters.csv")
    csv_bortezomib = csv_data[csv_data['name'] == 'bortezomib']
    
    # Query database data
    db_conn = DatabaseConnection()
    db_data = db_conn.execute_query("SELECT * FROM im_sprime_solved_s_prime WHERE name = 'bortezomib'")
    
    # Compare results
    print(f"CSV entries: {len(csv_bortezomib)}")
    print(f"Database entries: {len(db_data)}")
    
    # Check for exact matches
    # Check for closest matches
    # Report discrepancies
```

#### **2. Performance Comparison Tests**
```python
# Test script to compare performance
import time

def performance_test():
    # Test CSV loading time
    start_time = time.time()
    csv_result = get_single_testvalue()  # CSV version
    csv_time = time.time() - start_time
    
    # Test database query time
    start_time = time.time()
    db_result = get_single_testvalue_from_db()  # Database version
    db_time = time.time() - start_time
    
    print(f"CSV Time: {csv_time:.2f} seconds")
    print(f"Database Time: {db_time:.2f} seconds")
    print(f"Performance Improvement: {((csv_time - db_time) / csv_time) * 100:.1f}%")
```

#### **3. Data Accuracy Tests**
```python
# Test script to verify data accuracy
def accuracy_test():
    # Test if database values are within acceptable ranges
    # Test if calculations match expected formulas
    # Test if data types are correct
    # Test if all required fields are present
```

---

## 📋 **Action Items**

### **Immediate (This Week)**
- [ ] **Verify CSV data source and version**
- [ ] **Check database data source and version**
- [ ] **Implement closest match query as temporary solution**
- [ ] **Document exact discrepancy values**

### **Short-term (Next 2 Weeks)**
- [ ] **Investigate data migration process**
- [ ] **Compare total row counts between CSV and database**
- [ ] **Implement data validation tests**
- [ ] **Update migration documentation**

### **Long-term (Next Month)**
- [ ] **Establish data reconciliation process**
- [ ] **Implement automated data quality checks**
- [ ] **Create data versioning system**
- [ ] **Update migration strategy**

---

## 📞 **Contact Information**

**Primary Investigator**: [Your Name]  
**Project Lead**: [Project Lead Name]  
**Database Administrator**: [DBA Name]  
**Data Source Contact**: [Data Source Contact]

**Next Review Date**: [Date + 1 Week]  
**Status Update Required**: Yes

---

## 📎 **Appendices**

### **Appendix A: Database Schema**
```sql
-- Key tables used in investigation
im_sprime_solved_s_prime: Main table with pre-calculated S' values
- 603,981 total rows
- 479 bortezomib entries
- Pre-calculated fields: eff, eff_100, eff_ec50, s_prime
```

### **Appendix B: Query Examples**
```sql
-- All queries used in investigation
-- [Include all SQL queries from the investigation]
```

### **Appendix C: Data Samples**
```csv
-- Sample data from both CSV and database
-- [Include sample data for comparison]
```

---

**Report Generated**: January 2025  
**Version**: 1.0  
**Status**: ⚠️ **REQUIRES IMMEDIATE ATTENTION**

---

*This report documents the investigation of data discrepancies between CSV source data and PostgreSQL database during the DepMap migration project. All findings and recommendations should be reviewed by the project team before proceeding with the migration.*
