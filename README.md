# Property2024

This is a pet-project using data from the UK land registry website, wherefrom the original (public) dataset was downloaded. It had about 30 million records.
I wanted to produce a visual that shows property inflation rates across England and Wales at two levels of granularity; postcode area and individual property. 
Properties with a single transaction were removed. Records with missing info (e.g. postcode that no longer exists) were also removed. 
The code was written with assistance from Microsoft CoPilot and ChatGPT, however AI alone probably contributed about 70% of the code. 
The remainder was based on judgement and internet browsing.
Note that: 
  1/ Only the earliest and the most recent transactions for a property were used to derive an inflation rate. About 8 million records were available at this point. 
  2/ Inflation rates shown are annualised.
  3/ No minimum trading period was used; so if one made a 10% loss/gain over a week, the result will be an extreme and uninsightful value. (consider (90%/110%)^52 - 1!!!)
  4/ Shown dataset is only postcodes starting with SE1 for illustration purposes only. Full England/Wales dataset is available freely on request.
  5/ No distinction is made between commercial and residential, freehold/leasehold or any other possible differentiators. 

While I enjoyed learning about dash, dash-leaflet and uploading an app to a public domain, I did not find the dataset very insightful. It simply uses property price bought/sold. It says nothing about circumstances of transaction(s), fees, potential property development etc. As such, I am not sure it can be used much for prediction without significant judgement calls. If one can supply me with more information and some pointers, maybe I can produce some more interesting visuals.

You can see the results in action in the following address: 

https://property2024.onrender.com/

The slider on the top restricts the transactions shown to a smaller period.
Note, this will be very slow - when you press on a postcode-area marker, you may need to wait for a minute or two for the more detailed postcode-level (smaller markers) to appear. The longer the dataperiod (see strip at the top of the map), the longer it takes for the map to update.
If one of the smaller markers corresponds to a single record, hovering over it will show the relevant info. If the marker relates to many records, information for each record will appear on a table upon clicking on the marker.
The app is not optimised for a mobile phone screen.
If you want to run the code locally, on your own machine, I'm happy to supply detailed instructions, if you struggle to make the code work. In the very last line, you should set debug=True, so you can see error messages if you are struggling. 

Comments/suggestions welcome. Code produced on 12/12/2024.
