bool_temps=('0' '1')
xvars=('current' 'charge')
yvars=('width' 'HM_left')

for bool_temp in "${bool_temps[@]}"; do
    for xvar in "${xvars[@]}"; do
        for yvar in "${yvars[@]}"; do
            python3 plot_results_qinj_MDthesis.py --low_temp "$bool_temp" --xvar "$xvar" --yvar "$yvar"
            python3 plot_results_qinj_MDthesis.py --low_temp "$bool_temp" --xvar "$xvar" --yvar "$yvar" --group_plot
        done
    done
done