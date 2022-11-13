_is_afcfgr_given = False

filename = "company_data.txt"
#filename = "company_data.tx"

mandatory_fields = [
            'market_cap'
            ,'outstanding_shares'
            ,'pretax_income'
            ,'income_tax'
            ,'total_debt'	
            ,'interest_ex'
            ,'beta' 
            ,'free_cash_flows'   
            ,'avg_fcf_growth_rate'                    
            #,'test'
        ]

fields = []
values = []        
data = None

try:
    print(f"importing {filename}...")
    with open(filename) as fd:
        data = fd.read().strip().split("\n")
        for line in data:
            line = line.strip()
            field = line.split(":")[0]
            value = line.split(":")[1]

            if field in mandatory_fields[:6]:
                value = int(value.replace(",", ""))
            elif field == mandatory_fields[6]:  #== 'beta' 
                value = float(value.replace(",", ""))
            elif field == mandatory_fields[7]:  #== 'free_cash_flows'
                lst = value.split("\t")
                if len(lst) == 0: raise ValueError("missing value: free cash flows")
                value = [ int(x.replace(",", "")) for x in lst ]
            elif field == mandatory_fields[8]:  #=='avg_fcf_growth_rate'   
                if value != None and value != '':
                    value = float(value)
                    #if value >= 0 and value <= 1:
                    if 0 <= value <= 1:
                        _is_afcfgr_given = True
            else:
                value = value
            
            fields.append(field)
            values.append(value)

    for field in mandatory_fields:
        if not field in fields:
            raise ValueError(f"missing field: {field}")

    print(fields)
    print(values)

    print(f"is avg fcf gr: {_is_afcfgr_given}")

    print(f"{filename} import complete")
except IOError as err:
    print(err)
except:
    print("import failed")


"""data
market_cap:721,609,664
outstanding_shares:3,157,753
beta:2.11
pretax_income:6,343,000
income_tax:699,000
total_debt:33,723,000	
interest_ex:371,000
free_cash_flows:3,515,000	2,786,000	1,078,000	-3,000	-3,476,000
avg_fcf_growth_rate:
"""