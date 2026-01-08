This lab will require a Warehouse. Creating one beforehand is best.
1. From Snowsight -> Projects - Notebooks
2. From Top right (+ Notebooks)use the drop down and select "import .ipynb file"
3. Choose the automotive_synthetic.ipynb from the directory where you have cloned the repo
4. Change the name because many people will be using the same account
5. Change the Notebook Location to ADMIN_DB and Schema to PUBLIC
6. Leave Runtime as Run on Warehouse (default) and Runtime Version as "Snowflake Warehouse Runtime 2.0" (default)
7. Change the Query Warehouse to the Warehouse you created for yourself (It will still work with default, but you might have to wait if someone else is using the default)
8. Leave Notebook Warehouse as default. This is a warehouse that runs the Jupiter notebooks UI.

Press CREATE

9. The first two cell types needs to be updated to SQL type. Use the drop down in the top left of the cell that should be showing "Python", Select SQL instead - do this for the first two cells.
10. In the first cell locat the line that says 
SET DATABASE_NAME = 'FORD_AUTOMOTIVE_DB' 
Change it to make it unique, maybe replace the word FORD to your name or initials
11. In the Notebook navigation that is showing the name of your notebook, locate the plus sign (in front of search). This brings up a menu, select "Upload from Local"
12. The file to upload is part of the repository you cloned. Browse the Folders and select vins.txt, this file should become visible under notebook name. Notebook uses this file for referential integrity between tables.


You are all set to Run All or run the cells one by one.

