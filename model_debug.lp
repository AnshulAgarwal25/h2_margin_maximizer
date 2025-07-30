\* Source Pyomo model name=unknown *\

max 
objective:
+20.11 h2_amount(pipeline)
+20.11 h2_amount(bank)
+25.52 h2_amount(h2o2)
+15.3 h2_amount(flaker_1)
+15.3 h2_amount(flaker_2)
+15.3 h2_amount(flaker_3)
+15.3 h2_amount(flaker_4)
+4.41 h2_amount(boiler_p60)
+4.4 h2_amount(boiler_p120)

s.t.

c_u_total_h2_constraint_:
+1 h2_amount(pipeline)
+1 h2_amount(hcl)
+1 h2_amount(bank)
+1 h2_amount(h2o2)
+1 h2_amount(flaker_1)
+1 h2_amount(flaker_2)
+1 h2_amount(flaker_3)
+1 h2_amount(flaker_4)
+1 h2_amount(boiler_p60)
+1 h2_amount(boiler_p120)
+1 h2_amount(vent)
<= 22662.96

c_u_min_h2_allocation(pipeline)_:
-1 h2_amount(pipeline)
+10265.14 allocate(pipeline)
<= 0

c_u_min_h2_allocation(hcl)_:
-1 h2_amount(hcl)
+7151.81 allocate(hcl)
<= 0

c_u_min_h2_allocation(bank)_:
-1 h2_amount(bank)
<= 0

c_u_min_h2_allocation(h2o2)_:
-1 h2_amount(h2o2)
+3189.22 allocate(h2o2)
<= 0

c_u_min_h2_allocation(flaker_1)_:
-1 h2_amount(flaker_1)
<= 0

c_u_min_h2_allocation(flaker_2)_:
-1 h2_amount(flaker_2)
+2056.53 allocate(flaker_2)
<= 0

c_u_min_h2_allocation(flaker_3)_:
-1 h2_amount(flaker_3)
<= 0

c_u_min_h2_allocation(flaker_4)_:
-1 h2_amount(flaker_4)
<= 0

c_u_min_h2_allocation(boiler_p60)_:
-1 h2_amount(boiler_p60)
+900.0 allocate(boiler_p60)
<= 0

c_u_min_h2_allocation(boiler_p120)_:
-1 h2_amount(boiler_p120)
+1500.0 allocate(boiler_p120)
<= 0

c_u_min_h2_allocation(vent)_:
-1 h2_amount(vent)
<= 0

c_u_max_h2_allocation(pipeline)_:
+1 h2_amount(pipeline)
-10265.14 allocate(pipeline)
<= 0

c_u_max_h2_allocation(hcl)_:
+1 h2_amount(hcl)
-7151.81 allocate(hcl)
<= 0

c_u_max_h2_allocation(bank)_:
+1 h2_amount(bank)
-10244.7375 allocate(bank)
<= 0

c_u_max_h2_allocation(h2o2)_:
+1 h2_amount(h2o2)
-3189.22 allocate(h2o2)
<= 0

c_u_max_h2_allocation(flaker_1)_:
+1 h2_amount(flaker_1)
<= 0

c_u_max_h2_allocation(flaker_2)_:
+1 h2_amount(flaker_2)
-2056.53 allocate(flaker_2)
<= 0

c_u_max_h2_allocation(flaker_3)_:
+1 h2_amount(flaker_3)
<= 0

c_u_max_h2_allocation(flaker_4)_:
+1 h2_amount(flaker_4)
<= 0

c_u_max_h2_allocation(boiler_p60)_:
+1 h2_amount(boiler_p60)
-3500.0 allocate(boiler_p60)
<= 0

c_u_max_h2_allocation(boiler_p120)_:
+1 h2_amount(boiler_p120)
-6000.0 allocate(boiler_p120)
<= 0

c_u_max_h2_allocation(vent)_:
+1 h2_amount(vent)
-21932.399999999998 allocate(vent)
<= 0

c_e_mandatory_allocation(pipeline)_:
+1 allocate(pipeline)
= 1

c_e_mandatory_allocation(hcl)_:
+1 allocate(hcl)
= 1

c_e_mandatory_allocation(h2o2)_:
+1 allocate(h2o2)
= 1

c_e_mandatory_allocation(flaker_1)_:
+1 allocate(flaker_1)
= 1

c_e_mandatory_allocation(flaker_2)_:
+1 allocate(flaker_2)
= 1

c_u_flaker_restricted_upper(1)_:
+1 h2_amount(flaker_3)
-10000 flaker_range_mode(flaker_3)
<= 0

c_u_flaker_exact_max_lower(1)_:
-1 h2_amount(flaker_3)
+10000 flaker_range_mode(flaker_3)
<= 10000

c_u_flaker_exact_max_upper(1)_:
+1 h2_amount(flaker_3)
+10000 flaker_range_mode(flaker_3)
<= 10000

bounds
   0 <= h2_amount(pipeline) <= +inf
   0 <= h2_amount(hcl) <= +inf
   0 <= h2_amount(bank) <= +inf
   0 <= h2_amount(h2o2) <= +inf
   0 <= h2_amount(flaker_1) <= +inf
   0 <= h2_amount(flaker_2) <= +inf
   0 <= h2_amount(flaker_3) <= +inf
   0 <= h2_amount(flaker_4) <= +inf
   0 <= h2_amount(boiler_p60) <= +inf
   0 <= h2_amount(boiler_p120) <= +inf
   0 <= h2_amount(vent) <= +inf
   0 <= allocate(pipeline) <= 1
   0 <= allocate(hcl) <= 1
   0 <= allocate(bank) <= 1
   0 <= allocate(h2o2) <= 1
   0 <= allocate(flaker_1) <= 1
   0 <= allocate(flaker_2) <= 1
   0 <= allocate(boiler_p60) <= 1
   0 <= allocate(boiler_p120) <= 1
   0 <= allocate(vent) <= 1
   0 <= flaker_range_mode(flaker_3) <= 1
binary
  allocate(pipeline)
  allocate(hcl)
  allocate(bank)
  allocate(h2o2)
  allocate(flaker_1)
  allocate(flaker_2)
  allocate(boiler_p60)
  allocate(boiler_p120)
  allocate(vent)
  flaker_range_mode(flaker_3)
end
