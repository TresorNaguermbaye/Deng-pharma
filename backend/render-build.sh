if [ -f "data_dump_final_clean.json" ]; then
    echo "✅ data_dump_final_clean.json trouvé ! Taille : $(ls -lh data_dump_final_clean.json | awk '{print $5}')"
else
    echo "❌ data_dump_final_clean.json INTROUVABLE !"
    exit 1
fi

python manage.py loaddata data_dump_final_clean.json --ignorenonexistent