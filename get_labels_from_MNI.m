
%{
Code originally written by Julien Dirani in Cortical Systems Lab

Updated on 4/15/25 by Kamron Soldozy for his own preprocessing use

This code will produce an out_EMUXXX.xlsx file for each tsv file located in
the 'original_datadir' specified below. It uses the MNI coordinates from
brainstorm and the mni2atlas function (must be added to path) to convert
those coordinates to actual brain regions.

%}


selected_atlases = [1, 2, 3, 9];% MNI Structural Atlas (9)
                            % Harvard-Oxford Cortical Structural Atlas (2)

                       
% Get all subject files
original_datadir = '/Users/kamronsoldozy/Documents/PhD/ANALYSIS/DATA/MNI_FILES/';
filePattern = fullfile(original_datadir, 'EMU*.tsv');
files = dir(filePattern);


% Loop over file paths
for fileIdx = 1:length(files)
    % Get the input file name
    inputFname = files(fileIdx).name;
    inputPath = fullfile(original_datadir, inputFname);
    
    % Generate the output file name
    [~, baseName, ~] = fileparts(inputPath);
    outputFile = [original_datadir, 'out_', baseName, '.xlsx'];
    
    % Read the excel
    data = readtable(inputPath, "FileType", "text",'Delimiter', '\t');

    % Check if the table contains the 'MNI' column
    if ~ismember('MNI', data.Properties.VariableNames)
        error('The CSV file must contain a column named "MNI".');
    end
    
    % Process each row and dynamically create columns
    numRows = height(data);
    dynamicCols = struct();
    
    for i = 1:numRows
        % Extract MNI coordinates as a numeric array
        mniStr = data.MNI{i}; % Assuming 'MNI' column is in cell format with coordinates as strings
        mniCoords = str2num(mniStr); %#ok<ST2NM> % Convert string to numeric array
        
        if isempty(mniCoords) || numel(mniCoords) ~= 3 % Check if row is empty.
            warning('Invalid MNI coordinates at row %d. Skipping.', i);
            continue;
        end
    
        % Call mni2atlas
        atlasResult = mni2atlas(mniCoords, selected_atlases);
        
        % Loop through each element in the struct array and populate dynamic columns
        for j = 1:numel(atlasResult)
            colName = matlab.lang.makeValidName(atlasResult(j).name); % Ensure column names are valid
            if ~isfield(dynamicCols, colName)
                dynamicCols.(colName) = repmat({''}, numRows, 1); % Initialize with empty cells
            end
            dynamicCols.(colName){i} = atlasResult(j).label; % Populate the column
        end
    end
    
    % Convert the struct of dynamic columns into a table
    dynamicColsTable = struct2table(dynamicCols);
    
    % Combine the original table with the new dynamic columns
    updatedData = [data, dynamicColsTable];
    
    % Write the updated table to a new CSV file
    writetable(updatedData, outputFile);
    disp(['Updated CSV file written to ', outputFile]);
end
