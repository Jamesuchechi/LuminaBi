from rest_framework import serializers
from .models import Visualization, VisualizationComment, VisualizationTag, VisualizationFavorite


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = VisualizationComment
        fields = ['id', 'user', 'user_full_name', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisualizationTag
        fields = ['id', 'name']
        read_only_fields = ['id']


class VisualizationSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    tag_count = serializers.SerializerMethodField()
    favorite_count = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Visualization
        fields = [
            'id',
            'owner',
            'title',
            'description',
            'chart_type',
            'config',
            'dataset',
            'created_at',
            'updated_at',
            'is_public',
            'comments',
            'tags',
            'comment_count',
            'tag_count',
            'favorite_count',
            'is_favorited',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_tag_count(self, obj):
        return obj.tags.count()

    def get_favorite_count(self, obj):
        return obj.favorites.count()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return VisualizationFavorite.objects.filter(
                visualization=obj,
                user=request.user
            ).exists()
        return False
