#---------------------------------------------------------------------------------------------------------
#-------Import-----------
#----------------------------------------------------------------------------------------------------------

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import logout as auth_logout
from .models import UserProfile
import pandas as pd
import re
from rapidfuzz import process, fuzz
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

# Enhanced function to parse .env file
def load_env(env_path: str = '.env') -> Dict[str, str]:
    config = {}
    if not Path(env_path).exists():
        print(f"Warning: {env_path} not found. Using empty config.")
        return config
    
    with open(env_path, 'r', encoding='utf-8') as f:
        in_multiline = False
        current_key = None
        current_value = []
        
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip empty or comment lines
            
            # Handle multiline values (basic, ends at next key or EOF)
            if in_multiline:
                if '=' in line and not line.startswith(' ' * (len(current_key) + 1)):  # New key starts
                    config[current_key] = ' '.join(current_value).strip().strip('"\'')
                    current_key = None
                    in_multiline = False
                else:
                    current_value.append(line)
                    continue
            
            if '=' in line:
                parts = line.split('=', 1)
                key = parts[0].strip()
                value_part = parts[1].strip()
                
                # Handle quoted values
                if (value_part.startswith('"') and value_part.endswith('"')) or \
                   (value_part.startswith("'") and value_part.endswith("'")):
                    value = value_part[1:-1]
                else:
                    value = value_part
                
                if value.endswith('\\'):  # Simple multiline indicator
                    in_multiline = True
                    current_key = key
                    current_value = [value[:-1]]  # Remove \
                else:
                    config[key] = value
            else:
                print(f"Warning: Invalid line {line_num}: {line}")
    
    # Handle any pending multiline
    if current_key:
        config[current_key] = ' '.join(current_value).strip().strip('"\'')
    
    return config

# Load config from .env once at module level
config = load_env()
report_url = config.get('report_url')
campaign_url = config.get('campaign_url')
master_path = config.get('master_path')

print("Loaded config:")
for k, v in config.items():
    print(f"  {k}: {v}") 


# --------------------------------------------------------------------------------------
                  #--------------login page----------------      
# --------------------------------------------------------------------------------------
def user_login(request):
    # Redirect if already authenticated (check both Django auth and custom session)
    if request.user.is_authenticated or 'username' in request.session:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Server-side validation: Ensure both fields are provided
        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return render(request, 'login.html')

        try:
            user = UserProfile.objects.get(username=username)
            if check_password(password, user.password):
                # Use Django's login for better session handling (optional but recommended)
                # from django.contrib.auth import login
                # login(request, user)  # If UserProfile is compatible with Django User
                # Or stick with custom:
                request.session['username'] = user.username
                messages.success(request, f"Welcome, {user.username}!")
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
        except UserProfile.DoesNotExist:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html')


#---------------------------------------------------------------------------------------------------------
                            #---------------------logout------------------------
#----------------------------------------------------------------------------------------------------------

def user_logout(request):
    auth_logout(request)  # Use Django's logout to clear session and auth
    # Clear custom session key as well
    if 'username' in request.session:
        del request.session['username']
    request.session.flush()  # Fully clear the session
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')



# -----------------------------------------------------------------------------------------------------   
               #--------------home page----------------
# ------------------------------------------------------------------------------------------------------

def home(request):
    username = request.session.get('username')  # safer way to access session
    if username:
        return render(request, 'home.html', {'username': username})
    else:
        messages.error(request, "Please log in first.")
        return redirect('login')

# -----------------------------------------------------------------------------------------------------   
               #--------------Logout----------------
# ------------------------------------------------------------------------------------------------------
def user_logout(request):
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')




#---------------------------------------------------------------------------------------------------------
                            #-------comman variables  starts-----------
#----------------------------------------------------------------------------------------------------------


sponsor_list = ['BSK','CFW','DAG','DFO','EFL','GWM','LLS','Madrivo','NIW','PDS','W4','W4E']

# Normalization
def normalize_string(s, sponsors=None):
    import re

    if not isinstance(s, str):
        s = str(s)

    s = s.lower().strip()

    # Remove sponsor tags (same as your original)
    if sponsors:
        for sponsor in sponsors:
            s = s.replace(f"_{sponsor.lower()}_", "_")
            s = s.replace(f"_{sponsor.lower()}", "")

    # ✅ Remove trailing numeric suffixes (e.g., _1703, _002, etc.)
    s = re.sub(r'_\d+$', '', s)

    # Split into parts
    parts = s.split('_')
    cleaned_parts = []

    for part in parts:
        # Keep numbers that are internal (like 2024), skip meaningless numeric parts
        if re.fullmatch(r'\d+', part):
            # Skip only if it's not a year-like pattern (e.g., not 2024)
            if not (len(part) == 4 and part.startswith(('19', '20'))):
                continue
        cleaned_parts.append(part)

    return '_'.join(cleaned_parts)


# Fuzzy match
def fuzzy_match_datafiles(report_df, master_df, threshold=80):
    report_df['original_datafile_clean'] = report_df['original_datafile'].fillna('').apply(
        lambda x: normalize_string(x, sponsors=sponsor_list)
    )
    master_df['Data File Clean'] = master_df['Data File'].fillna('').apply(lambda x: normalize_string(x))
    all_files = master_df['Data File Clean'].unique().tolist()
    matches, scores = [], []
    for df_name in report_df['original_datafile_clean']:
        match, score, _ = process.extractOne(df_name, all_files, scorer=fuzz.token_sort_ratio)
        matches.append(match if score >= threshold else '')
        scores.append(score)
    report_df['matched_datafile'] = matches
    report_df['match_score'] = scores
    return report_df

import re  # Move this to top-level imports if not already

def normalize_string(s, sponsors=None):
    if not isinstance(s, str):
        s = str(s)

    s = s.lower().strip()

    # Remove sponsor tags
    if sponsors:
        for sponsor in sponsors:
            s = s.replace(f"_{sponsor.lower()}_", "_")
            s = s.replace(f"_{sponsor.lower()}", "")

    # Remove trailing numeric suffixes
    s = re.sub(r'_\d+$', '', s)

    # Split into parts
    parts = s.split('_')
    cleaned_parts = []

    for part in parts:
        # Keep numbers that are internal (like 2024), skip meaningless numeric parts
        if re.fullmatch(r'\d+', part):
            # Skip only if it's not a year-like pattern
            if not (len(part) == 4 and part.startswith(('19', '20'))):
                continue
        cleaned_parts.append(part)

    return '_'.join(cleaned_parts)

# Fuzzy match (fixed unpacking and return both DataFrames)
def fuzzy_match_datafiles(report_df, master_df, threshold=80):
    report_df['original_datafile_clean'] = report_df['original_datafile'].fillna('').apply(
        lambda x: normalize_string(x, sponsors=sponsor_list)
    )
    master_df['Data File Clean'] = master_df['Data File'].fillna('').apply(lambda x: normalize_string(x))
    all_files = master_df['Data File Clean'].unique().tolist()
    matches, scores = [], []
    for df_name in report_df['original_datafile_clean']:
        result = process.extractOne(df_name, all_files, scorer=fuzz.token_sort_ratio)
        if result:
            # Robust unpack: handle 2 or 3 elements
            match = result[0]
            score = result[1]
        else:
            match, score = '', 0
        matches.append(match if score >= threshold else '')
        scores.append(score)
    report_df['matched_datafile'] = matches
    report_df['match_score'] = scores
    return report_df, master_df



def normalize_string(s, sponsors=None):
    import re

    if not isinstance(s, str):
        s = str(s)

    s = s.lower().strip()

    # Remove sponsor tags (same as your original)
    if sponsors:
        for sponsor in sponsors:
            s = s.replace(f"_{sponsor.lower()}_", "_")
            s = s.replace(f"_{sponsor.lower()}", "")

    # ✅ Remove trailing numeric suffixes (e.g., _1703, _002, etc.)
    s = re.sub(r'_\d+$', '', s)

    # Split into parts
    parts = s.split('_')
    cleaned_parts = []

    for part in parts:
        # Keep numbers that are internal (like 2024), skip meaningless numeric parts
        if re.fullmatch(r'\d+', part):
            # Skip only if it's not a year-like pattern (e.g., not 2024)
            if not (len(part) == 4 and part.startswith(('19', '20'))):
                continue
        cleaned_parts.append(part)

    return '_'.join(cleaned_parts)

def fuzzy_match_datafiles(report_df, master_df, threshold=80):
    report_df['original_datafile_clean'] = report_df['original_datafile'].fillna('').apply(
        lambda x: normalize_string(x, sponsors=sponsor_list)
    )
    master_df['Data File Clean'] = master_df['Data File'].fillna('').apply(lambda x: normalize_string(x))
    all_files = master_df['Data File Clean'].unique().tolist()
    matches, scores = [], []
    for df_name in report_df['original_datafile_clean']:
        match, score, _ = process.extractOne(df_name, all_files, scorer=fuzz.token_sort_ratio)
        matches.append(match if score >= threshold else '')
        scores.append(score)
    report_df['matched_datafile'] = matches
    report_df['match_score'] = scores
    return report_df



#--------------------------------------------AI Recommentation-----------------------------------------------

#---------------------------------------------------------------------------------------------------------
                            #-------recommendation Logic-----------
#----------------------------------------------------------------------------------------------------------
# Updated recommendation logic
import os
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Enhanced function to parse .env file (add this if not already in your views.py)
def load_env(env_path: str = '.env') -> Dict[str, str]:
    config = {}
    if not Path(env_path).exists():
        print(f"Warning: {env_path} not found. Using empty config.")
        return config
    
    with open(env_path, 'r', encoding='utf-8') as f:
        in_multiline = False
        current_key = None
        current_value = []
        
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip empty or comment lines
            
            # Handle multiline values (basic, ends at next key or EOF)
            if in_multiline:
                if '=' in line and not line.startswith(' ' * (len(current_key) + 1)):  # New key starts
                    config[current_key] = ' '.join(current_value).strip().strip('"\'')
                    current_key = None
                    in_multiline = False
                else:
                    current_value.append(line)
                    continue
            
            if '=' in line:
                parts = line.split('=', 1)
                key = parts[0].strip()
                value_part = parts[1].strip()
                
                # Handle quoted values
                if (value_part.startswith('"') and value_part.endswith('"')) or \
                   (value_part.startswith("'") and value_part.endswith("'")):
                    value = value_part[1:-1]
                else:
                    value = value_part
                
                if value.endswith('\\'):  # Simple multiline indicator
                    in_multiline = True
                    current_key = key
                    current_value = [value[:-1]]  # Remove \
                else:
                    config[key] = value
            else:
                print(f"Warning: Invalid line {line_num}: {line}")
    
    # Handle any pending multiline
    if current_key:
        config[current_key] = ' '.join(current_value).strip().strip('"\'')
    
    return config

# Load config from .env once (module-level, assuming this is in views.py)
config = load_env()
report_url = config.get('report_url')
campaign_url = config.get('campaign_url')
master_path = config.get('master_path')  # Note: Your code uses File2.xlsx; adjust env if needed or use this

print("Loaded config:")
for k, v in config.items():
    print(f"  {k}: {v}")

def recommend_campaigns_with_datafiles(merged_df, sort_by, top_n_campaigns=10, top_n_files=5):
    merged_df = merged_df.copy()
    merged_df['clicks'] = pd.to_numeric(merged_df.get('clicks', 0), errors='coerce').fillna(0)
    merged_df['sent'] = pd.to_numeric(merged_df.get('sent', 0), errors='coerce').fillna(0)
    merged_df['revenue'] = pd.to_numeric(merged_df.get('revenue', 0), errors='coerce').fillna(0)
    merged_df['cpm'] = pd.to_numeric(merged_df['cpm'], errors='coerce').fillna(0)
    merged_df['epc'] = merged_df['revenue'] / merged_df['clicks'].replace(0, 1)
    if sort_by == 'performance':
        merged_df['perf'] = merged_df['revenue'] / merged_df['sent'].replace(0, 1)

    # Determine aggregation for campaigns
    if sort_by == 'revenue':
        agg_dict = {'revenue': 'sum'}
        sort_col = 'revenue'
        file_sort_col = 'revenue'
        file_agg = 'sum'
    elif sort_by == 'epc':
        agg_dict = {'epc': 'mean'}
        sort_col = 'epc'
        file_sort_col = 'epc'
        file_agg = 'mean'
    elif sort_by == 'cpm':
        agg_dict = {'cpm': 'mean'}
        sort_col = 'cpm'
        file_sort_col = 'cpm'
        file_agg = 'mean'
    elif sort_by == 'performance':
        agg_dict = {'perf': 'mean'}
        sort_col = 'perf'
        file_sort_col = 'perf'
        file_agg = 'mean'

    top_campaigns = (
        merged_df.groupby('campaign_name')
        .agg(agg_dict)
        .reset_index()
        .sort_values(by=sort_col, ascending=False)
        .head(top_n_campaigns)
    )

    all_files = []
    for camp in top_campaigns['campaign_name']:
        sub = merged_df[merged_df['campaign_name'] == camp].copy()
        sub = sub[['matched_datafile', 'cpm', 'DF Count', 'last_send_date', file_sort_col]].dropna(subset=['matched_datafile'])
        sub = sub.drop_duplicates(subset='matched_datafile')

        # Aggregate per file if needed
        agg_cols = {
            file_sort_col: file_agg,
            'cpm': 'mean',
            'DF Count': 'first',  # Consistent from master
            'last_send_date': 'max'
        }
        sub_agg = sub.groupby('matched_datafile').agg(agg_cols).reset_index()
        sub_agg = sub_agg.sort_values(by=file_sort_col, ascending=False).head(top_n_files)
        sub_agg['campaign_name'] = camp
        all_files.append(sub_agg)

    all_files_df = pd.concat(all_files, ignore_index=True) if all_files else pd.DataFrame()
    return top_campaigns, all_files_df

def recommendations(request):
    if request.method == 'POST':
        campaign_name = request.POST.get('campaign_name', '').lower().strip()
        min_engagement_str = request.POST.get('min_engagement', '')
        min_engagement = float(min_engagement_str) / 100 if min_engagement_str else 0
        sort_by = request.POST.get('sort_by', 'revenue')
        limit = int(request.POST.get('limit', 10))
        notes = request.POST.get('notes', '')
    else:
        campaign_name = ''
        min_engagement = 0
        sort_by = 'revenue'
        limit = 10
        notes = ''

    # Load data using .env vars
    if not master_path or not Path(master_path).exists():
        return render(request, 'recommendations.html', {'error': 'Master data file not found at path from .env.'})
    master_df = pd.read_excel(master_path)
    master_df.rename(columns=lambda x: x.strip(), inplace=True)
    master_df['Data File Clean'] = master_df['Data File'].fillna('').apply(lambda x: normalize_string(x))

    if not report_url:
        return render(request, 'recommendations.html', {'error': 'Report URL not configured in .env.'})
    report_resp = requests.get(report_url)
    report_resp.raise_for_status()  # Raise error on bad status
    report = pd.DataFrame(report_resp.json()['data'])
    
    if not campaign_url:
        return render(request, 'recommendations.html', {'error': 'Campaign URL not configured in .env.'})
    campaign_resp = requests.get(campaign_url)
    campaign_resp.raise_for_status()  # Raise error on bad status
    campaign = pd.DataFrame(campaign_resp.json()['data'])

    # Clean
    report, _ = fuzzy_match_datafiles(report, master_df)  # Unpack both, ignore master
    report['offer_date'] = pd.to_datetime(report['offer_date'], format='%d-%m-%Y', errors='coerce')
    report['campaign_name'] = report['campaign_name'].astype(str).str.lower().str.strip()
    campaign['campaign_name'] = campaign['campaign_name'].astype(str).str.lower().str.strip()

    merged = pd.merge(report, campaign, on='campaign_name', how='inner')
    merged = pd.merge(merged, master_df, left_on='matched_datafile', right_on='Data File Clean', how='left')

    last_send = (
        merged.dropna(subset=['campaign_name', 'matched_datafile', 'offer_date'])
        .groupby(['campaign_name', 'matched_datafile'])['offer_date']
        .max()
        .reset_index()
        .rename(columns={'offer_date': 'last_send_date'})
    )
    merged = pd.merge(merged, last_send, on=['campaign_name', 'matched_datafile'], how='left')

    # Compute metrics
    merged['clicks'] = pd.to_numeric(merged.get('clicks', 0), errors='coerce').fillna(0)
    merged['sent'] = pd.to_numeric(merged.get('sent', 0), errors='coerce').fillna(0)
    merged['revenue'] = pd.to_numeric(merged.get('revenue', 0), errors='coerce').fillna(0)
    merged['epc'] = merged['revenue'] / merged['clicks'].replace(0, 1)
    merged['engagement'] = (merged['clicks'] / merged['sent'].replace(0, 1)) * 100
    merged['cpm'] = pd.to_numeric(merged['cpm'], errors='coerce').fillna(0)

    # Apply filters
    if min_engagement > 0:
        merged = merged[merged['engagement'] >= min_engagement]
    if campaign_name:
        merged = merged[merged['campaign_name'].str.contains(campaign_name, na=False)]

    # Generate recommendations
    top_campaigns, all_files_df = recommend_campaigns_with_datafiles(merged, sort_by, top_n_campaigns=limit, top_n_files=5)

    # Group files by campaign for template
    grouped_files = []
    for camp in top_campaigns['campaign_name']:
        camp_files = all_files_df[all_files_df['campaign_name'] == camp].to_dict('records')
        grouped_files.append({
            'campaign_name': camp,
            'files': camp_files
        })

    # Campaign options for select
    campaign_options = sorted(merged['campaign_name'].dropna().unique())

    context = {
        'grouped_files': grouped_files,
        'campaign_options': campaign_options,
        'form_data': {
            'campaign_name': campaign_name,
            'min_engagement': min_engagement * 100 if min_engagement > 0 else '',
            'sort_by': sort_by,
            'limit': limit,
            'notes': notes,
        }
    }
    return render(request, 'recommendations.html', context)

#--------------------------------------------AI Recommentation Ends-----------------------------------------------

#------------------------Un Used File ------------------------


# -----------------------------
# Mail Logic
# -----------------------------
def unuse_DS(request):
    # Use loaded .env vars (assuming config is loaded at module level)
    if not master_path or not Path(master_path).exists():
        return render(request, 'unuse_DS.html', {'error': 'Master data file not found at path from .env.'})
    master_df = pd.read_excel(master_path)
    master_df.columns = master_df.columns.str.strip()

    # Fetch APIs using .env vars
    if not report_url:
        return render(request, 'unuse_DS.html', {'error': 'Report URL not configured in .env.'})
    report_resp = requests.get(report_url)
    report_resp.raise_for_status()  # Raise error on bad status
    report_df = pd.DataFrame(report_resp.json()['data'])
    
    if not campaign_url:
        return render(request, 'unuse_DS.html', {'error': 'Campaign URL not configured in .env.'})
    campaign_resp = requests.get(campaign_url)
    campaign_resp.raise_for_status()  # Raise error on bad status
    campaign_df = pd.DataFrame(campaign_resp.json()['data'])

    # Date handling
    possible_date_cols = ['date', 'offer_date', 'Offer Date', 'after_suppression_date', 'created_at']
    date_col = next((col for col in possible_date_cols if col in report_df.columns), None)
    if date_col:
        report_df['date'] = pd.to_datetime(report_df[date_col], errors='coerce', dayfirst=True)
        report_df = report_df.dropna(subset=['date']).sort_values(by='date', ascending=False).reset_index(drop=True)
    else:
        return render(request, 'unuse_DS.html', {'error': 'No valid date column found in report data.'})

    # Step 1: Fuzzy Match
    report_df, master_df = fuzzy_match_datafiles(report_df, master_df, threshold=80)

    # Step 2: Merge with Master
    merged_df = pd.merge(
        report_df, master_df,
        left_on='matched_datafile', right_on='Data File Clean', how='left'
    )

    # Step 3: Merge with Campaign
    merged_df = pd.merge(
        merged_df, campaign_df,
        on='campaign_name', how='left', suffixes=('', '_campaign')
    )

    # Filter options
    isp_options = sorted(master_df['ISP Name'].dropna().unique().tolist())
    file_series_options = sorted(master_df['File Series'].dropna().unique().tolist())

    unused_datafiles = []
    summary = None

    if request.method == "POST":
        campaign_id = request.POST.get("campaign_id", "").strip()
        isp_selected = request.POST.get("isp_selected", "All")
        file_series_selected = request.POST.get("file_series_selected", "All")
        days_slider = int(request.POST.get("days_slider", 15))

        cutoff_date = datetime.today() - timedelta(days=days_slider)

        if campaign_id:
            campaign_match = campaign_df[campaign_df['campaign_id'].astype(str) == campaign_id]
            if not campaign_match.empty:
                campaign_name = campaign_match.iloc[0]['campaign_name']

                filtered_master_df = master_df.copy()
                if isp_selected != "All":
                    filtered_master_df = filtered_master_df[filtered_master_df['ISP Name'] == isp_selected]
                if file_series_selected != "All":
                    filtered_master_df = filtered_master_df[filtered_master_df['File Series'] == file_series_selected]

                all_datafiles = filtered_master_df['Data File Clean'].dropna().unique()

                recent_used_files = report_df[
                    (report_df['campaign_name'] == campaign_name) &
                    (report_df['date'] >= cutoff_date)
                ]['matched_datafile'].dropna().unique()

                unused_datafiles = sorted(list(set(all_datafiles) - set(recent_used_files)))
                summary = {
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "days": days_slider,
                    "count": len(unused_datafiles)
                }
            else:
                summary = {"error": "No campaign found with that ID."}

    context = {
        "isp_options": isp_options,
        "file_series_options": file_series_options,
        "unused_datafiles": unused_datafiles,
        "summary": summary,
    }

    return render(request, "unuse_DS.html", context)

def logout(request):
    raise NotImplementedError

def logout(request):
    raise NotImplementedError


#------------------------------------------------------------------------------------------------------------
# ------------------------Un Used File  ends------------------------
#------------------------------------------------------------------------------------------------------------





#------------------------------------------------------------------------------------------------------------
#---------------------------------------------best file ----------------------------------------------------
#------------------------------------------------------------------------------------------------------------


def best_files_view(request):
    # Use loaded .env vars (assuming config is loaded at module level)
    if not report_url:
        return render(request, "best_files.html", {"error": 'Report URL not configured in .env.'})
    if not campaign_url:
        return render(request, "best_files.html", {"error": 'Campaign URL not configured in .env.'})
    if not master_path or not Path(master_path).exists():
        return render(request, "best_files.html", {"error": 'Master data file not found at path from .env.'})

    context = {"error": None, "results": None, "message": None}

    try:
        # Load data using .env vars
        report_resp = requests.get(report_url)
        report_resp.raise_for_status()  # Raise error on bad status
        campaign_resp = requests.get(campaign_url)
        campaign_resp.raise_for_status()  # Raise error on bad status
        campaign_df = pd.DataFrame(campaign_resp.json()['data'])
        report_df = pd.DataFrame(report_resp.json()['data'])
        master_df = pd.read_excel(master_path)

        # Clean column names
        campaign_df.columns = campaign_df.columns.str.strip()
        report_df.columns = report_df.columns.str.strip()
        master_df.columns = master_df.columns.str.strip()

        # Fuzzy match (now returns both)
        report_df, master_df = fuzzy_match_datafiles(report_df, master_df)

        # Parse offer_date
        if 'offer_date' in report_df.columns:
            report_df['offer_date'] = pd.to_datetime(report_df['offer_date'], format='%d-%m-%Y', errors='coerce')

        # Merge report and campaign
        merged_df = pd.merge(report_df, campaign_df, on='campaign_name', how='left')

        # Merge with master for ISP
        isp_merge = master_df[['Data File Clean', 'ISP Name']].drop_duplicates()
        merged_df = pd.merge(
            merged_df,
            isp_merge,
            left_on='matched_datafile',
            right_on='Data File Clean',
            how='left'
        )

        # Compute last send date
        if 'offer_date' in merged_df.columns and 'matched_datafile' in merged_df.columns:
            last_send_df = (
                merged_df.dropna(subset=['matched_datafile', 'offer_date'])
                .groupby('matched_datafile')['offer_date']
                .max()
                .reset_index(name='last_send_date')
            )
            merged_df = pd.merge(merged_df, last_send_df, on='matched_datafile', how='left')

        # Filters from GET params
        sponsor_selected = request.GET.get("sponsor", "All")
        category_selected = request.GET.get("category", "All")
        isp_selected = request.GET.get("isp", "All")
        exclude_days = int(request.GET.get("exclude_days", 0))

        filtered_df = merged_df.copy()

        # Apply filters safely (check column existence)
        if 'sponsor' in filtered_df.columns and sponsor_selected != "All":
            filtered_df = filtered_df[filtered_df['sponsor'] == sponsor_selected]
        if 'category' in filtered_df.columns and category_selected != "All":
            filtered_df = filtered_df[filtered_df['category'] == category_selected]
        if 'ISP Name' in filtered_df.columns and isp_selected != "All":
            filtered_df = filtered_df[filtered_df['ISP Name'] == isp_selected]

        # Exclude last X days
        if exclude_days > 0 and 'last_send_date' in filtered_df.columns:
            cutoff_date = datetime.now() - timedelta(days=exclude_days)
            filtered_df = filtered_df[
                (filtered_df['last_send_date'].isna()) | (filtered_df['last_send_date'] < cutoff_date)
            ]

        # Convert numeric columns safely
        numeric_cols = ['revenue', 'cpm', 'epc', 'clicks', 'sent']
        for col in numeric_cols:
            if col in filtered_df.columns:
                filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0)

        # Group and summarize
        if not filtered_df.empty and 'matched_datafile' in filtered_df.columns:
            # Drop NaN files for grouping
            valid_df = filtered_df.dropna(subset=['matched_datafile'])
            if not valid_df.empty:
                grouped = valid_df.groupby('matched_datafile').agg({
                    'revenue': 'sum',
                    'cpm': 'mean',
                    'epc': 'mean',
                    'clicks': 'sum',
                    'sent': 'sum'
                }).reset_index().sort_values(by='revenue', ascending=False)

                top_records = grouped.head(15).to_dict(orient='records')
                best_file = grouped.iloc[0]['matched_datafile'] if not grouped.empty else None

                # Filter options (with "All")
                sponsor_options = ["All"] + sorted(campaign_df['sponsor'].dropna().unique().tolist()) if 'sponsor' in campaign_df.columns else ["All"]
                category_options = ["All"] + sorted(campaign_df['category'].dropna().unique().tolist()) if 'category' in campaign_df.columns else ["All"]
                isp_options = ["All"] + sorted(master_df['ISP Name'].dropna().unique().tolist()) if 'ISP Name' in master_df.columns else ["All"]

                # Restructure context to match template (filters dict)
                filters = {
                    'sponsors': sponsor_options,
                    'categories': category_options,
                    'isps': isp_options,
                    'selected': {
                        'sponsor': sponsor_selected,
                        'category': category_selected,
                        'isp': isp_selected,
                        'exclude_days': exclude_days
                    }
                }

                context.update({
                    "results": top_records,
                    "best_file": best_file,
                    "record_count": len(filtered_df),
                    "unique_files": len(grouped),
                    "filters": filters  # This fixes the dropdown listing
                })
                return render(request, "best_files.html", context)

        context["message"] = "No data found for the selected filters."

    except Exception as e:
        context["error"] = str(e)

    # Fallback filters if error (empty options to avoid crashes)
    context["filters"] = {
        'sponsors': ["All"],
        'categories': ["All"],
        'isps': ["All"],
        'selected': {
            'sponsor': "All",
            'category': "All",
            'isp': "All",
            'exclude_days': 0
        }
    }

    return render(request, "best_files.html", context)



#------------------------------------------------------------------------------------------------------------
#---------------------------------------------best file ends------------------------------------------------
#------------------------------------------------------------------------------------------------------------



