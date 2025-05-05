#!/usr/bin/env python3

def fix_indentation():
    print("Fixing indentation in enhanced_backtesting.py...")
    
    # Read the file
    with open('enhanced_backtesting.py', 'r') as f:
        lines = f.readlines()
    
    # Create a new file with fixed indentation
    with open('enhanced_backtesting_fixed.py', 'w') as f:
        i = 0
        while i < len(lines):
            line = lines[i]
            # Check for specific areas with indentation issues
            if 160 <= i <= 180 or 240 <= i <= 260:
                # Fix common indentation issues
                if line.strip().startswith('def ') and not line.startswith('    def '):
                    line = '    ' + line
                # Ensure content inside methods is properly indented
                elif line.strip() and not line.startswith('    '):
                    if i > 0 and lines[i-1].strip().startswith('def '):
                        line = '        ' + line.lstrip()
            
            f.write(line)
            i += 1
    
    print("Fixed file saved as enhanced_backtesting_fixed.py")
    print("Verify the fixed file and then rename it to replace the original.")

if __name__ == "__main__":
    fix_indentation() 